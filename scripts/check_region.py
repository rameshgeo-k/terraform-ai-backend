import boto3

model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

regions_to_check = ["us-east-1", "us-east-2", "us-west-2", "ap-south-1"]

for region in regions_to_check:
    try:
        bedrock = boto3.client("bedrock", region_name=region)
        response = bedrock.list_foundation_models(byProvider="Anthropic")
        
        available = any(model_id in m['modelId'] for m in response['modelSummaries'])
        status = "✅ AVAILABLE" if available else "❌ NOT AVAILABLE"
        print(f"{region:15} - {status}")
    except Exception as e:
        print(f"{region:15} - ❌ ERROR: {e}")
