# AgentCore Gateway Infrastructure Setup

## Architecture

```
Agent → AgentCore Gateway (Bedrock) → AWS API Gateway (REST) → VPC Link → NLB → ALB → fprtool ECS
```

Each layer:

| Layer | Purpose | Why needed |
|-------|---------|-----------|
| AgentCore Gateway | MCP protocol, semantic search, JWT auth | Standard MCP interface + tool discovery |
| AWS API Gateway | HTTP proxy with VPC Link | Bridges public AgentCore to private VPC |
| NLB (Network LB) | TCP:443 passthrough | Required by API GW VPC Link (only supports NLB) |
| ALB (fprtool-lbext) | TLS termination, routing | Existing infra, serves fprtool ECS tasks |

## Prod Resources

| Resource | ID / ARN | Notes |
|----------|----------|-------|
| AgentCore Gateway | `fpr-mcp-gateway-ghntgmtwjb` | CUSTOM_JWT auth, SEMANTIC search |
| AgentCore Target | `JZ3LSR9SUC` | Schema from S3 |
| API Gateway (REST) | `w73edrxlij` (fpr-mcp-gateway) | Stage: `prd` |
| VPC Link | `sajyrq` (fprtool-agentcore-vpclink) | Status: AVAILABLE |
| NLB | `fprtool-agentcore-nlb` | TCP:443, internal |
| Target Group | `fprtool-agentcore-tg` | Type: `alb`, target: fprtool-lbext |
| Schema S3 | `s3://bedrock-agentcore-runtime-348767535692-ap-southeast-1-837werwc9/schemas/fprtool-full.json` | |

| Config | Value |
|--------|-------|
| Account | `348767535692` (tvlk-fpr-prod) |
| Region | ap-southeast-1 |
| VPC | `vpc-00e37890f4239f76f` |
| Cognito Pool | `ap-southeast-1_NTrYoh9Zu` |
| Cognito Domain | `internal-id.ath.traveloka.com` |
| Allowed Clients | `3r7njgpcnuo8u260581rj6uho`, `i01t804ups4dme8p1kfoat8jb` |

## Staging Resources

| Resource | ID / ARN |
|----------|----------|
| AgentCore Gateway | `fpr-sysinteg-ai-gateway-ml342jgb92` |
| API Gateway | `tz0pqimy4l` |
| VPC Link | `f56zdo` (fprtool-agentcore-vpclink) |
| NLB | `fprtool-agentcore-nlb` (56524552ae98c59c) |
| Schema S3 | `s3://bedrock-agentcore-runtime-354767975881-ap-southeast-1-a1beixhzs/schemas/fprtool-full.json` |
| Account | `354767975881` (tvlk-fpr-stg) |

## Setup Steps (for new region/environment)

### 1. Create NLB + Target Group

```bash
# Create target group (type=alb, protocol=TCP, port=443)
aws elbv2 create-target-group \
  --name fprtool-agentcore-tg \
  --protocol TCP --port 443 \
  --target-type alb \
  --vpc-id <vpc-id> \
  --health-check-protocol TCP

# Register the fprtool ALB as target
aws elbv2 register-targets \
  --target-group-arn <tg-arn> \
  --targets "Id=<fprtool-lbext-arn>,Port=443"

# Create NLB (MUST be internal, same VPC as ALB)
aws elbv2 create-load-balancer \
  --name fprtool-agentcore-nlb \
  --type network --scheme internal \
  --subnets <private-subnet-1> <private-subnet-2> <private-subnet-3>

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn <nlb-arn> \
  --protocol TCP --port 443 \
  --default-actions Type=forward,TargetGroupArn=<tg-arn>
```

### 2. Fix Security Group (CRITICAL)

The fprtool ALB's security group must allow inbound from NLB subnets:

```bash
# Get NLB subnet CIDRs
aws ec2 describe-subnets --subnet-ids <nlb-subnets> --query "Subnets[].CidrBlock"

# Add to ALB security group
aws ec2 authorize-security-group-ingress \
  --group-id <alb-sg-id> \
  --ip-permissions '[{"IpProtocol":"tcp","FromPort":443,"ToPort":443,"IpRanges":[
    {"CidrIp":"<cidr-1>","Description":"NLB subnet (agentcore)"},
    {"CidrIp":"<cidr-2>","Description":"NLB subnet (agentcore)"},
    {"CidrIp":"<cidr-3>","Description":"NLB subnet (agentcore)"}
  ]}]'
```

⚠️ **This is the #1 gotcha.** Without this, NLB health checks fail and API GW returns 500.

### 3. Create VPC Link

```bash
aws apigateway create-vpc-link \
  --name fprtool-agentcore-vpclink \
  --target-arns <nlb-arn>

# Wait for AVAILABLE status (takes ~3-5 minutes)
aws apigateway get-vpc-link --vpc-link-id <id>
```

### 4. Create API Gateway

```bash
# Create REST API
aws apigateway create-rest-api --name fpr-mcp-gateway --endpoint-configuration types=REGIONAL

# Create /{proxy+} resource
aws apigateway create-resource --rest-api-id <id> --parent-id <root-id> --path-part "{proxy+}"

# Create ANY method
aws apigateway put-method --rest-api-id <id> --resource-id <proxy-id> \
  --http-method ANY --authorization-type NONE \
  --request-parameters '{"method.request.path.proxy":true}'

# Create VPC_LINK integration
aws apigateway put-integration --rest-api-id <id> --resource-id <proxy-id> \
  --http-method ANY --type HTTP_PROXY --integration-http-method ANY \
  --uri "https://<backend-domain>/{proxy}" \
  --connection-type VPC_LINK --connection-id <vpc-link-id> \
  --request-parameters '{"integration.request.path.proxy":"method.request.path.proxy"}'

# Deploy
aws apigateway create-deployment --rest-api-id <id> --stage-name prd
```

**Integration URI must match ALB certificate domain:**
- Prod fprtool-lbext cert: `*.fpr.traveloka.com` → use `tool-api.fpr.traveloka.com`
- Staging fprtool-lbext cert: `*.fpr.staging-traveloka.com` → use `tool-api.fpr.staging-traveloka.com`

### 5. Create AgentCore Gateway

```bash
aws bedrock-agentcore-control create-gateway \
  --name fpr-mcp-gateway \
  --role-arn <service-role-arn> \
  --authorizer-type CUSTOM_JWT \
  --authorizer-configuration '{"customJWTAuthorizer":{
    "discoveryUrl":"https://cognito-idp.<region>.amazonaws.com/<pool-id>/.well-known/openid-configuration",
    "allowedClients":["<client-id-1>","<client-id-2>"]
  }}' \
  --protocol-configuration '{"mcp":{"searchType":"SEMANTIC","supportedVersions":["2025-03-26"]}}'
```

### 6. Create Target (with S3 schema)

```bash
aws bedrock-agentcore-control create-gateway-target \
  --gateway-identifier <gateway-id> \
  --name fprtool-prod \
  --target-configuration '{"mcp":{"openApiSchema":{"s3":{"uri":"s3://<bucket>/schemas/fprtool-full.json"}}}}'
```

Schema format: standard OpenAPI 3.x with `servers[].url` pointing to the API GW stage URL.

### 7. Upload Schema

```bash
# Update servers URL in schema
cat fprtool-full.json | jq '.servers = [{"url":"https://<api-gw-id>.execute-api.<region>.amazonaws.com/<stage>"}]' > /tmp/schema.json

aws s3 cp /tmp/schema.json s3://<bucket>/schemas/fprtool-full.json
```

## Gotchas & Lessons Learned

1. **NLB → ALB security group**: NLB doesn't have its own SG. Traffic appears from NLB's private subnet IPs. Must whitelist those CIDRs on ALB SG.

2. **Wrong ALB target**: `fprtapi-lbint` ≠ `fprtool-lbext`. They're different services. `fprtapi` is an internal router that returns 404 for direct tool API calls. Always use `fprtool-lbext`.

3. **Integration URI must match ALB cert**: API GW sends SNI from the URI hostname through the NLB (TCP passthrough). If hostname doesn't match ALB cert, TLS handshake fails → 500.

4. **`tool-api.fpr.traveloka.com` is internal-only DNS**: Doesn't resolve publicly. That's fine — API GW uses it for SNI only, routing goes through VPC Link. Don't try to use it with INTERNET connection type.

5. **Target naming affects tool prefix**: Target name `fprtool-prod` → tools become `fprtool-prod___<op>`. Choose names carefully.

6. **Schema must be OpenAPI object, not array**: AgentCore target creation fails with "Cannot deserialize from Array" if you pass a JSON array of tools. Must be proper `{"openapi":"3.0.x","paths":{...}}` format.

7. **S3 schema reference works**: Use `{"s3":{"uri":"s3://..."}}` instead of inlining the full 130KB schema. Cleaner and easier to update.

8. **allowedClients on Gateway**: If using tokens from a different Cognito app client than what Gateway was configured with, update `allowedClients` array to include both.

## Updating Schema

When tools change (new endpoints, modified params):

```bash
# 1. Regenerate schema locally
# 2. Update servers URL
# 3. Upload to S3
aws s3 cp fprtool-full.json s3://<bucket>/schemas/fprtool-full.json

# 4. Reload target from the same S3 URI (forces re-read of schema)
aws bedrock-agentcore-control update-gateway-target \
  --gateway-identifier <gateway-id> \
  --target-id <target-id> \
  --name <target-name> \
  --target-configuration '{"mcp":{"openApiSchema":{"s3":{"uri":"s3://<bucket>/schemas/fprtool-full.json"}}}}'
```

## AWS Roles Required

| Role | Used For |
|------|----------|
| `Engineer@tvlk-fpr-prod` | Read ops: describe, list, get |
| `DeployerExt@tvlk-fpr-prod` | Create/modify: ELB, API GW, AgentCore, S3, EC2 SG |
