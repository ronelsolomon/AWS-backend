from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_logs as logs,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool
        user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="serverless-backend-users",
            self_sign_up_enabled=True,
            sign_in_aliases={"email": True},
            auto_verify={"email": True},
            password_policy={
                "min_length": 8,
                "require_lowercase": True,
                "require_uppercase": True,
                "require_digits": True,
                "require_symbols": True,
            },
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Add App Client
        user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool=user_pool,
            auth_flows={"admin_user_password": True, "user_password": True, "user_srp": True},
            o_auth={
                "flows": {"authorization_code_grant": True},
                "scopes": [cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                "callback_urls": ["http://localhost:3000/callback"],
                "logout_urls": ["http://localhost:3000"]
            }
        )

        # Create DynamoDB Table
        table = dynamodb.Table(
            self, "ItemsTable",
            table_name="serverless-items",
            partition_key={"name": "id", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "created_at", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Add GSI for querying by user
        table.add_global_secondary_index(
            index_name="user-index",
            partition_key={"name": "user_id", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "created_at", "type": dynamodb.AttributeType.STRING}
        )

        # Create Lambda execution role
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonCognitoReadOnly")
            ]
        )

        # Create Lambda function
        lambda_fn = _lambda.Function(
            self, "ApiHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
                "CLIENT_ID": user_pool_client.user_pool_client_id,
                "TABLE_NAME": table.table_name,
                "REGION": self.region
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # Grant Lambda access to DynamoDB
        table.grant_read_write_data(lambda_fn)

        # Create API Gateway with Cognito Authorizer
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # Create REST API
        api = apigw.RestApi(
            self, "ServerlessApi",
            default_cors_preflight_options={
                "allow_origins": apigw.Cors.ALL_ORIGINS,
                "allow_methods": apigw.Cors.ALL_METHODS,
                "allow_headers": ["Content-Type", "Authorization"],
                "allow_credentials": True
            },
            deploy_options={
                "stage_name": "prod",
                "logging_level": apigw.MethodLoggingLevel.INFO,
                "metrics_enabled": True
            }
        )

        # Add resources and methods
        items = api.root.add_resource("items")
        item = items.add_resource("{id}")

        # Add CORS preflight for OPTIONS
        self._add_cors_options(items)
        self._add_cors_options(item)

        # Integrate Lambda with API Gateway
        lambda_integration = apigw.LambdaIntegration(
            lambda_fn,
            proxy=True,
            integration_responses=[{"statusCode": "200"}]
        )

        # Add methods with Cognito authorization
        items.add_method("GET", lambda_integration, authorizer=authorizer)
        items.add_method("POST", lambda_integration, authorizer=authorizer)
        item.add_method("GET", lambda_integration, authorizer=authorizer)
        item.add_method("PUT", lambda_integration, authorizer=authorizer)
        item.add_method("DELETE", lambda_integration, authorizer=authorizer)

        # Outputs
        self.api_url = api.url
        self.user_pool_id = user_pool.user_pool_id
        self.user_pool_client_id = user_pool_client.user_pool_client_id

    def _add_cors_options(self, resource):
        resource.add_method(
            'OPTIONS',
            apigw.MockIntegration(
                integration_responses=[{
                    'statusCode': '200',
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'OPTIONS,GET,PUT,POST,DELETE'"
                    }
                }],
                passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
                request_templates={"application/json": "{statusCode: 200}"}
            ),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            }]
        )
