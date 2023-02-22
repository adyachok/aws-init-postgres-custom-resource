import os
from pathlib import Path

from aws_cdk import (
    Duration,
    aws_iam as _iam,
    aws_rds as _rds,
    aws_lambda as _lambda,
    aws_ec2 as _ec2,
    aws_lambda_python_alpha as _plambda
)

import aws_cdk.aws_logs as _logs
from constructs import Construct


class MyDBInitLambdaConstruct(Construct):

    def __init__(self,
                 scope: Construct,
                 construct_id: str,
                 db: _rds.DatabaseInstance,
                 db_security_group: _ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        account_id = os.getenv('AWS_ACCOUNT_ID')
        if not account_id:
            raise Exception('You have to provide AWS account id!')

        availability_zone = self.node.try_get_context('props').get('availabilityZone')
        if not availability_zone:
            raise Exception('You have to provide AWS availability zone.')

        database_name = self.node.try_get_context('props')['databaseName']
        if not database_name:
            raise Exception('You have to provide database name.')

        lambda_db_init_role = _iam.Role(self,
                                        'myDbInitLambdaRole',
                                        assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com')
                                        )
        # https://bobbyhadz.com/blog/aws-lambda-provided-execution-role-does-not-have-permissions
        # https://bobbyhadz.com/blog/aws-cdk-policy-arn-does-not-exist-error
        lambda_db_init_role.add_managed_policy(
            _iam.ManagedPolicy.from_managed_policy_name(
                self,
                'lambdaRunSQLQueryPolicy',
                managed_policy_name='my-lambda-run-sql-policy'
            ))

        lambda_db_init_role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'))
        # lambda_db_init_role.add_managed_policy(
        #     _iam.ManagedPolicy.from_aws_managed_policy_name('AWSLambdaVPCAccessExecutionRole'))

        lambda_code = Path(__file__).parent.joinpath('lambda_code').joinpath('init_test_db')

        if not lambda_code.exists() and not lambda_code.is_dir():
            raise Exception('Cannot find lambda code to init test database.')

        python_layer = _plambda.PythonLayerVersion(
            self,
            'Psycopg2LambdaLayer',
            entry=str(lambda_code.parent.joinpath('python')),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description='Psycopg2 Library',
            layer_version_name='postgresql-psycopg-python-lambda-layer'
        )

        self.on_event = _lambda.Function(self,
                                         'myInitTestDbLambda',
                                         function_name='my-init-test-db-lambda',
                                         runtime=_lambda.Runtime.PYTHON_3_9,
                                         vpc=db.vpc,
                                         role=lambda_db_init_role,
                                         code=_lambda.Code.from_asset(str(lambda_code)),
                                         handler='app.lambda_handler',
                                         layers=[python_layer],
                                         log_retention=_logs.RetentionDays.ONE_DAY,
                                         timeout=Duration.minutes(3),
                                         security_groups=[db_security_group],
                                         environment={
                                             'DB_USERNAME': db.secret.secret_value_from_json(
                                                 'username').unsafe_unwrap(),
                                             'DB_PASSWORD': db.secret.secret_value_from_json(
                                                 'password').unsafe_unwrap(),
                                             'DB_HOST': db.db_instance_endpoint_address,
                                             'DB_NAME': db.secret.secret_value_from_json(
                                                 'database').unsafe_unwrap()
                                         }
                                         )

        # self.on_event = _plambda.PythonFunction(
        #     self,
        #     'myInitTestDbLambda',
        #     function_name='my-init-test-db-lambda',
        #     runtime=_lambda.Runtime.PYTHON_3_9,
        #     vpc=db.vpc,
        #     role=lambda_db_init_role,
        #     entry=str(lambda_code),
        #     index='app.python',
        #     handler='lambda_handler',
        #     log_retention=_logs.RetentionDays.ONE_DAY,
        #     timeout=Duration.minutes(3),
        #     security_groups=[db_security_group],
        #     layers=[python_layer],
        #     environment={
        #         'DB_USERNAME': db.secret.secret_value_from_json(
        #             'username').unsafe_unwrap(),
        #         'DB_PASSWORD': db.secret.secret_value_from_json(
        #             'password').unsafe_unwrap(),
        #         'DB_HOST': db.db_instance_endpoint_address,
        #         'DB_NAME': db.secret.secret_value_from_json(
        #             'database').unsafe_unwrap()
        #     }
        # )

        # https://www.youtube.com/watch?v=3f0gkBEo7Jc&t=1s
        # https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#images-create-from-base
        # https://dev.to/wesleycheek/deploy-a-docker-built-lambda-function-with-aws-cdk-fio
        # self.on_event = _lambda.DockerImageFunction(
        #     self,
        #     id='myInitDbLambda',
        #     function_name='my-init-db-lambda',
        #     code=_lambda.DockerImageCode.from_image_asset(
        #         directory=str(lambda_code)
        #     ),
        #     vpc=db.vpc,
        #     security_groups=[db_security_group],
        #     timeout=Duration.minutes(3),
        #     log_retention=_logs.RetentionDays.ONE_DAY,
        #     environment={
        #         'DB_USERNAME': db.secret.secret_value_from_json(
        #             'username').unsafe_unwrap(),
        #         'DB_PASSWORD': db.secret.secret_value_from_json(
        #             'password').unsafe_unwrap(),
        #         'DB_HOST': db.db_instance_endpoint_address,
        #         'DB_NAME': db.secret.secret_value_from_json(
        #             'database').unsafe_unwrap()
        #     }
        # )
        db_security_group.connections.allow_from(self.on_event,
                                                 _ec2.Port.tcp(5432),
                                                 'Test DB creation lambda ingress 5432'
                                                 )
