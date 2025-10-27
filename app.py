#!/usr/bin/env python3
from aws_cdk import App, Environment
from backend.backend_stack import BackendStack
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = App()

# Get environment variables
account = os.getenv('CDK_DEFAULT_ACCOUNT')
region = os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
env = Environment(account=account, region=region)

# Create stack
BackendStack(
    app,
    "ServerlessBackendStack",
    env=env,
    description="Serverless backend with Cognito, API Gateway, Lambda, and DynamoDB"
)

app.synth()
