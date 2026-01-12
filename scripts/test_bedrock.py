#!/usr/bin/env python
"""Test Bedrock model availability."""

import boto3
from botocore.exceptions import ClientError

# Your config
region = "ap-south-1"
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

print(f"Testing Bedrock in region: {region}")
print(f"Model ID: {model_id}")
print("-" * 50)

try:
    # Create Bedrock client
    bedrock = boto3.client("bedrock", region_name=region)
    
    # List foundation models
    print("\n✅ Bedrock client created successfully")
    print("\nListing available Anthropic models in", region)
    
    response = bedrock.list_foundation_models(
        byProvider="Anthropic"
    )
    
    print(f"\nFound {len(response['modelSummaries'])} Anthropic models:")
    for model in response['modelSummaries']:
        print(f"  - {model['modelId']}")
        if model_id in model['modelId']:
            print(f"    ✅ FOUND: {model['modelName']}")
    
    # Check if specific model exists
    model_found = any(model_id in m['modelId'] for m in response['modelSummaries'])
    
    if not model_found:
        print(f"\n❌ Model '{model_id}' NOT found in {region}")
        print("\nTry one of these instead:")
        for model in response['modelSummaries'][:5]:
            print(f"  - {model['modelId']}")
    else:
        print(f"\n✅ Model '{model_id}' is available!")
        
        # Test invoke
        print("\nTesting model invocation...")
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
        
        import json
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": "Say 'test successful' in one word"}
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        print(f"✅ Response: {result}")

except ClientError as e:
    error_code = e.response['Error']['Code']
    error_msg = e.response['Error']['Message']
    print(f"\n❌ AWS Error ({error_code}): {error_msg}")
    
    if error_code == "AccessDeniedException":
        print("\n💡 Solution: Request model access in AWS Bedrock console")
        print(f"   1. Go to: https://console.aws.amazon.com/bedrock/home?region={region}")
        print("   2. Click 'Model access' in left sidebar")
        print("   3. Click 'Modify model access'")
        print("   4. Enable Anthropic Claude models")
        print("   5. Submit and wait for approval (usually instant)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
