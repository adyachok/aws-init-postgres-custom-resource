from aws_cdk import (
    Stack,
    aws_ec2 as _ec2,
    aws_iam as _iam,
)
from constructs import Construct


class MyCustomRolesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: _ec2.Vpc, **kwargs) -> None:
        """Creates PostgreSQL database instance for the project."""
        super().__init__(scope, construct_id, **kwargs)

        database_name = self.node.try_get_context('props').get('databaseName')

        self.sql_policy = _iam.ManagedPolicy(self,
                                        'myLambdaRunSQLPolicy',
                                        managed_policy_name='my-lambda-run-sql-policy',
                                        statements=[_iam.PolicyStatement(
                                            effect=_iam.Effect.ALLOW,
                                            actions=[
                                                'rds-data:ExecuteStatement',
                                                'rds-data:RollbackTransaction',
                                                'rds-data:CommitTransaction',
                                                'rds-data:ExecuteSql',
                                                'rds-data:BatchExecuteStatement',
                                                'rds-data:BeginTransaction',
                                                'ec2:DescribeNetworkInterfaces',
                                                'ec2:CreateNetworkInterface',
                                                'ec2:DeleteNetworkInterface',
                                                'ec2:DescribeInstances',
                                                'ec2:AttachNetworkInterface',
                                                'ec2:DetachNetworkInterface',
                                                'ec2:ModifyNetworkInterfaceAttribute',
                                                'ec2:ResetNetworkInterfaceAttribute',
                                                'ec2:AssignPrivateIpAddresses',
                                                'ec2:UnassignPrivateIpAddresses',
                                                'logs:CreateLogGroup',
                                                'logs:CreateLogStream',
                                                'logs:PutLogEvents'
                                            ],
                                            # It makes sense to create more fine-grained permission later
                                            # Specifying subnet in which DB instance will be located
                                            # Resource for subnet
                                            # "arn:aws:rds:us-east-1:202441101000:subgrp:default-vpc-0c0ba805507e1f975"
                                            resources=[
                                                # f'arn:aws:rds:*:{account_id}:db:*'
                                                '*'
                                            ],
                                            conditions={
                                                "ForAllValues:StringEquals":
                                                    {
                                                        'aws:SourceVpc': f'{vpc.vpc_id}',
                                                        'rds:DatabaseName': f'{database_name}'
                                                    }
                                            }

                                        )])

