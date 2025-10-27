# AWS Serverless Backend

A production-ready AWS serverless backend with Cognito authentication, API Gateway, Lambda, and DynamoDB, built with AWS CDK and Python.

## ✨ Features

- 🔒 **Authentication**: JWT-based authentication with Amazon Cognito
- 🚀 **Serverless**: Fully managed services with automatic scaling
- 🏗 **Infrastructure as Code**: AWS CDK for reliable deployments
- 🔄 **RESTful API**: Complete CRUD operations with validation
- 📊 **Monitoring**: Built-in CloudWatch logging and metrics
- 🔐 **Security**: IAM roles with least privilege, input validation
- 🌐 **CORS Support**: Pre-configured for web applications
- 🧪 **Testing**: Unit and integration test setup
- 🔧 **Developer Experience**: Local development and debugging support

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16.x+ (for CDK)
- AWS CLI configured with admin permissions
- AWS CDK v2 installed (`npm install -g aws-cdk`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/aws-serverless-backend.git
   cd aws-serverless-backend
   ```

2. **Set up Python virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dev.txt
   npm install
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS account and region
   ```

## 🏗 Project Structure

```
.
├── app.py                     # CDK application entry point
├── backend/
│   └── backend_stack.py      # Main CDK stack definition
├── lambda/
│   ├── lambda_function.py    # Lambda function handler
│   └── requirements.txt      # Lambda dependencies
├── tests/                    # Unit and integration tests
├── .env.example              # Example environment variables
├── package.json              # Node.js dependencies
└── requirements-dev.txt      # Development dependencies
```

## 🚀 Deployment

### First-time Setup

```bash
# Bootstrap CDK in your AWS account (first time only)
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

### Deploy to AWS

```bash
# Deploy the stack
cdk deploy

# Deploy to a specific stage (dev/staging/prod)
cdk deploy --context stage=prod
```

### Deploy Outputs

After successful deployment, you'll receive:
- API Gateway URL
- Cognito User Pool ID
- Cognito Client ID
- DynamoDB Table Name

## 🔧 Local Development

### Run Lambda Locally

```bash
# Install local dependencies
pip install -r lambda/requirements.txt

# Set environment variables
export TABLE_NAME=local-table
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Start local API Gateway and Lambda
sam local start-api
```

### Test API Endpoints

```bash
# Register a new user
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# Get authentication token
TOKEN=$(curl -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}' | jq -r '.token')

# Access protected endpoints
curl -H "Authorization: Bearer $TOKEN" $API_URL/items
```

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/unit -v
```

### Run Integration Tests

```bash
# Deploy to a test environment
cdk deploy --context stage=test

# Run integration tests
pytest tests/integration -v
```

## 🛡 Security

- **Authentication**: JWT tokens with Cognito
- **Authorization**: IAM roles with least privilege
- **Data Protection**: Encryption at rest and in transit
- **Input Validation**: Pydantic models for all API inputs
- **Secrets Management**: AWS Secrets Manager or Parameter Store for sensitive data

## 📊 Monitoring and Logging

- **CloudWatch Logs**: All Lambda function logs
- **CloudWatch Metrics**: API Gateway and Lambda metrics
- **X-Ray Tracing**: Distributed tracing enabled
- **Error Tracking**: Structured error logging

## 🔄 CI/CD (GitHub Actions)

Pre-configured GitHub Actions workflows for:
- Linting and type checking on PRs
- Unit tests on push
- Automated deployments to staging/production

## 🧹 Cleanup

To remove all AWS resources:

```bash
cdk destroy
# Or for a specific stage
cdk destroy --context stage=prod
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🎓 Learning Path

### Core AWS Services

1. **AWS CDK (Cloud Development Kit)**
   - **What it is**: Framework for defining cloud infrastructure using familiar programming languages
   - **Key Concepts**:
     - Constructs: Basic building blocks (like `Stack`, `Table`, `Function`)
     - Stacks: Units of deployment
     - Environments: AWS account/region combinations
   - **Example**: `BackendStack` in `backend_stack.py` defines all resources

2. **AWS Lambda**
   - **What it is**: Serverless compute service
   - **Key Concepts**:
     - Handler function: Entry point for execution
     - Runtime: Python 3.9 in our case
     - Environment variables: Secure configuration
   - **Example**: `lambda_function.py` contains the request handler

3. **Amazon API Gateway**
   - **What it is**: Managed service for creating and managing APIs
   - **Key Concepts**:
     - REST API: Resource-based HTTP endpoints
     - Integration: Connection to Lambda functions
     - Authorizers: JWT validation with Cognito
   - **Example**: Defined in `backend_stack.py` with CORS and authentication

4. **Amazon DynamoDB**
   - **What it is**: NoSQL database service
   - **Key Concepts**:
     - Tables: Collections of items
     - Items: Individual records
     - GSIs: Global Secondary Indexes for flexible querying
   - **Example**: `ItemsTable` in `backend_stack.py`

5. **Amazon Cognito**
   - **What it is**: User authentication and authorization
   - **Key Concepts**:
     - User Pools: User directories
     - App Clients: Application configurations
     - JWT Tokens: Secure authentication
   - **Example**: `UserPool` and `UserPoolClient` in `backend_stack.py`

### Python Concepts

1. **Pydantic Models**
   ```python
   class ItemCreate(BaseModel):
       name: str
       description: str
   ```
   - Used for request/response validation
   - Automatic type conversion
   - Schema documentation

2. **AWS Lambda Powertools**
   - `@logger.inject_lambda_context`: Structured logging
   - `@tracer.capture_lambda_handler`: Distributed tracing
   - `@metrics.log_metrics`: Custom metrics

3. **Error Handling**
   ```python
   try:
       # Code that might fail
   except ClientError as e:
       # Handle AWS service errors
   except Exception as e:
       # Handle unexpected errors
   ```

### Security Concepts

1. **IAM Roles & Policies**
   - Least privilege principle
   - Managed policies vs. inline policies
   - Service roles for AWS services

2. **JWT Authentication**
   - Token-based authentication flow
   - Claims validation
   - Token expiration and refresh

### Best Practices

1. **Infrastructure as Code**
   - Version controlled infrastructure
   - Repeatable deployments
   - Environment parity

2. **Serverless Architecture**
   - Event-driven design
   - Stateless functions
   - Managed services where possible

## 📄 Documentation & Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [AWS Lambda Python Guide](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Amazon API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
- [Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Serverless Best Practices](https://docs.aws.amazon.com/whitepapers/latest/serverless-architectures-lambda/best-practices.html)
