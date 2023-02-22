import json

from aws_cdk import (
    Stack,
    aws_rds as _rds,
    aws_ec2 as _ec2,
    aws_secretsmanager as _secretmanager, Duration,
)
from constructs import Construct

from aws_init_postgres_custom_resource.constructs.dc_db_init_provider_constract import MyDBInitConstruct


class MyDBStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: _ec2.Vpc, **kwargs) -> None:
        """Creates PostgreSQL database instance for the project."""
        super().__init__(scope, construct_id, **kwargs)

        database_username = self.node.try_get_context('props')['databaseUsername']
        if not database_username:
            raise Exception('You have to provide database username.')

        database_name = self.node.try_get_context('props')['databaseName']
        if not database_name:
            raise Exception('You have to provide database name.')

        self.db_secret = _secretmanager.Secret(self,
                                          'dcRDSSecret',
                                          secret_name='dc_rds_secret',
                                          description='This secret contains database credentials.',
                                          generate_secret_string=_secretmanager.SecretStringGenerator(
                                              secret_string_template=json.dumps({
                                                  'username': database_username,
                                                  'database': database_name
                                              }),
                                              generate_string_key='password',
                                              exclude_punctuation=True,
                                              include_space=False
                                          )
                                          )

        db_creds = _rds.Credentials.from_secret(self.db_secret)

        # Security groups

        self.db_connection_group = _ec2.SecurityGroup(self, 'Proxy to RDS Connection', vpc=vpc)
        self.db_connection_group.add_ingress_rule(self.db_connection_group, _ec2.Port.tcp(5432))

        lambda_to_proxy_group = _ec2.SecurityGroup(self, 'Lambda to RDS Proxy', vpc=vpc)
        self.db_connection_group.add_ingress_rule(lambda_to_proxy_group, _ec2.Port.tcp(5432))

        # RDS
        self.db = _rds.DatabaseInstance(self,
                                        'mylDb',
                                        instance_identifier='my-db',
                                        credentials=db_creds,
                                        instance_type=_ec2.InstanceType.of(
                                            _ec2.InstanceClass.BURSTABLE3,
                                            _ec2.InstanceSize.MICRO),
                                        engine=_rds.DatabaseInstanceEngine.POSTGRES,
                                        allocated_storage=6,
                                        vpc=vpc,
                                        security_groups=[self.db_connection_group],
                                        database_name=database_name,
                                        deletion_protection=False,
                                        delete_automated_backups=True,
                                        backup_retention=Duration.days(1),
                                        )

        # RDS Proxy
        self.db_proxy = self.db.add_proxy('dbProxy',
                                          borrow_timeout=Duration.seconds(30),
                                          secrets=[self.db.secret],
                                          vpc=vpc,
                                          security_groups=[self.db_connection_group],
                                          require_tls=False
                                          )
        MyDBInitConstruct(self, 'MyDBInitConstruct',
                                   db=self.db,
                                   db_security_group=self.db_connection_group)

