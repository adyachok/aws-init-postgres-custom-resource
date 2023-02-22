#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_init_postgres_custom_resource.dc_db_stack import MyDBStack
from aws_init_postgres_custom_resource.dc_roles_stack import MyCustomRolesStack
from aws_init_postgres_custom_resource.dc_vpc_stack import MyVpcStack

app = cdk.App()

# 1. Create project's VPC
vpc_stack = MyVpcStack(app, 'DarkCrystalVpcStack')
# 2. Create custom roles
MyCustomRolesStack(app, 'DarkCrystalCustomRolesStack', vpc=vpc_stack.vpc)
# 3. Create project's database
db_stack = MyDBStack(app, 'DarkCrystalDBStack', vpc=vpc_stack.vpc)

app.synth()
