#!/usr/bin/env python
"""Test Bedrock streaming + LangChain ChatBedrock wrapper."""

import boto3
import json
from langchain_aws import ChatBedrock

# ----------------------------
# SETTINGS (replace with your settings.* values)
# ----------------------------
REGION = "us-east-1"   # Claude 3 is NOT available in us-east-1 or ap-south-1
MODEL_ID = "us.anthropic.claude-3-sonnet-20240229-v1:0"
PROVIDER = "anthropic"
TEMPERATURE = 0.7

# OPTIONAL: if you're assuming an IAM role
AWS_ROLE_ARN = "arn:aws:bedrock:us-east-1:393078901209:application-inference-profile/yn5pfw0heio3"
AWS_PROFILE_NAME = None   # e.g. "default"

# ----------------------------
# LANGCHAIN WRAPPER
# ----------------------------
print("\n" + "=" * 50)
print("Testing LangChain ChatBedrock")
print("=" * 50)

try:

    llm = ChatBedrock(
        model=AWS_ROLE_ARN,
        provider=PROVIDER,
        region_name=REGION,
        model_kwargs={
            "temperature": TEMPERATURE,
            "max_tokens": 200,
        },
        streaming=True
    )

    print("\nTesting LangChain streaming...")
    for chunk in llm.stream("Say hello in one word"):
        print(chunk.content, end="", flush=True)

    print("\n\n✅ LangChain streaming works!")

except Exception as e2:
    print(f"\n❌ LangChain Error: {e2}")
    import traceback
    traceback.print_exc()
