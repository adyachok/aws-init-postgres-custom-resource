from aws_cdk import (
    aws_iam as _iam,
    aws_rds as _rds,
    aws_ec2 as _ec2,
    CustomResource,
    RemovalPolicy
)
import aws_cdk.custom_resources as _custom_resources
import aws_cdk.aws_logs as _logs
from constructs import Construct

from aws_init_postgres_custom_resource.constructs.dc_db_init_lambda_constact import MyDBInitLambdaConstruct


class MyDBInitConstruct(Construct):

    def __init__(self,
                 scope: Construct,
                 construct_id: str,
                 db: _rds.DatabaseInstance,
                 db_security_group:_ec2.SecurityGroup,
                 **kwargs) -> None:
        """Creates PostgreSQL database instance for the project."""
        super().__init__(scope, construct_id, **kwargs)

        call_init_db_lambda_role = _iam.Role(self,
                                             'myCallLambdaInitDBRole',
                                             assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com')
                                             )

        lambda_construct = MyDBInitLambdaConstruct(self,
                                                            'MyDBInitLambdaConstruct',
                                                            db=db,
                                                            db_security_group=db_security_group
                                                            )

        # - Redundant with AWSLambda_FullAccess
        # call_init_db_lambda_stmt = _iam.Policy(self,
        #                                        'myCallLambdaInitDBRolePolicy',
        #                                        statements=[_iam.PolicyStatement(
        #                                            effect=_iam.Effect.ALLOW,
        #                                            resources=[lambda_construct.on_event.function_arn],
        #                                            actions=[
        #                                                'lambda:InvokeFunction'
        #                                            ]
        #                              y          )])
        #
        # call_init_db_lambda_role.attach_inline_policy(call_init_db_lambda_stmt)
        # - End redundant block

        call_init_db_lambda_role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name('AWSLambda_FullAccess'))

        # https://medium.com/cyberark-engineering/custom-resources-with-aws-cdk-d9a8fad6b673
        # https://github.com/felipeloha/aws-init-db/blob/main/lib/aws-init-db-stack.js
        # https://github.com/royby-cyberark/aws-custom-resource-demo/blob/master/cdk/cdk/s3_object_custom_resource.py
        # https://www.tecracer.com/blog/2021/05/implementing-and-deploying-custom-resources-using-cdk.html
        provider = _custom_resources.Provider(self,
                                              'myDBInitProvider',
                                              on_event_handler=lambda_construct.on_event,
                                              role=call_init_db_lambda_role,
                                              # log_retention=_logs.RetentionDays.ONE_DAY,
                                              provider_function_name='my-db-init-function',
                                              # vpc=db.vpc
                                              )

        cr = CustomResource(self,
                       'myDbInitCustomResource',
                       service_token=provider.service_token,
                       removal_policy=RemovalPolicy.DESTROY
                       )
        # https://felipelopezhamann.medium.com/initialize-an-rds-instance-on-creation-with-cdk-f2e5440918aa
        cr.node.add_dependency(db)
