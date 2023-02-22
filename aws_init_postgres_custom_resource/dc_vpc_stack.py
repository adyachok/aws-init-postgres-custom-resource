from aws_cdk import (
    Stack,
    aws_ec2 as _ec2,
)
from constructs import Construct


class MyVpcStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Creates Virtual Private Cloud for the project.

        On the current moment a VPC is using default properties.
        This code will create a VPC with 2 subnets (public and private)
        in every availability zone.
        """
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = _ec2.Vpc(self,
                            'MyVpc',
                            vpc_name='my-vpc',
                            max_azs=2
                            )
