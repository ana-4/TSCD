import boto3
from moto import mock_aws


@mock_aws
def create_mock_rds_instance():
    # Initialize a boto3 client for RDS
    client = boto3.client('rds', region_name='us-east-1')

    # Create a mock RDS instance
    response = client.create_db_instance(
        DBInstanceIdentifier='git-radar-metrics-db',
        DBInstanceClass='db.t3.micro',
        Engine='mysql',
        MasterUsername='masteruser',
        MasterUserPassword='masterpassword',
        AllocatedStorage=20
    )

    # Print the response
    print("DB Instance Created:", response['DBInstance']['DBInstanceIdentifier'])


if __name__ == "__main__":
    create_mock_rds_instance()
