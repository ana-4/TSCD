import boto3
from moto import mock_aws
import pytest


@pytest.fixture
def rds_client():
    with mock_aws():
        yield boto3.client('rds', region_name='us-east-1')


def test_create_rds_instance(rds_client):
    # Create a mock RDS instance
    response = rds_client.create_db_instance(
        DBInstanceIdentifier='git-radar-metrics-db',
        DBInstanceClass='db.t3.micro',
        Engine='mysql',
        MasterUsername='masteruser',
        MasterUserPassword='masterpassword',
        AllocatedStorage=20
    )

    # Verify the response
    assert response['DBInstance']['DBInstanceIdentifier'] == 'git-radar-metrics-db'


def test_describe_rds_instance(rds_client):
    # Create a mock RDS instance
    rds_client.create_db_instance(
        DBInstanceIdentifier='git-radar-metrics-db',
        DBInstanceClass='db.t3.micro',
        Engine='mysql',
        MasterUsername='masteruser',
        MasterUserPassword='masterpassword',
        AllocatedStorage=20
    )

    # Describe the mock RDS instance
    response = rds_client.describe_db_instances(DBInstanceIdentifier='git-radar-metrics-db')

    # Verify the response
    assert len(response['DBInstances']) == 1
    assert response['DBInstances'][0]['DBInstanceIdentifier'] == 'git-radar-metrics-db'
