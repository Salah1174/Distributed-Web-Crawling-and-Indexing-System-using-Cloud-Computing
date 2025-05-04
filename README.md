# Distributed-Web-Crawling-and-Indexing-System-using-Cloud-Computing
## Team Members
> - Mohamed Salah
> - Salma Hisham
> - Youssef Tamer
> - Salma Youssef

-----

## Overview

This project implements a distributed web crawling and indexing system using cloud computing services. The system is designed to efficiently crawl web pages, extract metadata, and store the results in a scalable and searchable format. It leverages AWS services such as SQS, RDS, and S3 for communication, storage, and processing.

----

## System Architecture
The system consists of the following components:

1. Client Node: Sends seed URLs and search queries to the system.
2. Master Node: Manages the distribution of crawling tasks to Crawler Nodes. It interacts with an RDS database to store and update the status of URLs and ensures that duplicate URLs are not processed. It also sends tasks to the TaskQueue for Crawler Nodes.
3. Crawler Nodes: Perform web crawling, extract metadata, and store results in S3.
4. Indexer Node: Processes crawled data, stores it in RDS, and handles search queries.

---

## Key Features
- Distributed crawling with support for multiple nodes.
- Metadata extraction and storage in AWS RDS.
- Search functionality with results delivered via AWS SQS.
- Scalable architecture leveraging AWS cloud services.
- Fault tolerance with heartbeat monitoring, retry logic, deduplication, and error handling.
- Autoscaling for the Worker Nodes (crawlers and indexers) based on workload.

***

## Steps to Use
### 1. Prerequisites

- AWS account with access to SQS, RDS, and S3.
- Python 3.8+ installed on all nodes.
- Required Python libraries installed:

```bash
pip install boto3 pymysql flask flask-cors scrapy 
```

### 2. Setting Up AWS Resources

1. Create SQS Queues:

    - Client_Master_Queue: For seed URLs.
    - SearchQueue: For search queries.
    - ResultQueue: For crawled data.
    - SearchResponseQueue: For search results.
    - IndexerStatusQueue: For heartbeat monitoring of the Indexer Node.

2. Set Up RDS:

    - Create an RDS instance and create a database .
    - Use the following schema for the "indexed_data" table used by the Indexer node to store indexed data:
        ```SQL 
                CREATE TABLE indexed_data (
                url VARCHAR(255) NOT NULL,
                title VARCHAR(255),
                description TEXT,
                keywords TEXT,
                s3_key VARCHAR(255),
                s3_bucket VARCHAR(255),
                PRIMARY KEY (url)
            ); 
            ```
    - Create another schema for the URLS table used by the Master Node:
        ```SQL
            CREATE TABLE Urls (
            url VARCHAR(255) NOT NULL,
            status ENUM('NEW', 'CRAWLED', 'INDEXED', 'ERROR') NOT NULL,
            depth INT NOT NULL,
            PRIMARY KEY (url)
            );
        ```

3. Create an S3 Bucket:

    - Store crawled HTML files in the bucket.

4. Configure IAM Roles:

    - Ensure all nodes have the necessary permissions to access SQS, RDS, and S3.

### 3. Running the System

**Client Node**
1. Start the Flask server:
```python
python Client_Backend.py 
```
2. Access the client interface via the public IP of the server:
> http://<PUBLIC_IP>:5000
3. Submit a seed URL and depth or a search query.

**Master Node**
1. Start the Master Node script:
```python
 python master.py
```
2. Monitor the Client_Master_Queue for incoming tasks.

**Crawler Nodes**
1. Start the crawler script
```python
 python crawling_spider.py
```
2. Ensure the crawler retrieves tasks from the TaskQueue and uploads results to S3.

**Indexer Node**
1. Start the indexer script
```python
 python main.py
```

Alternatively, Deploy the Worker Nodes as a systemd service:
```linux
sudo systemctl start indexer.service
```

2. Monitor the ResultQueue and SearchQueue for messages.

***

## Autoscaling 
1. Launch Template:
- Create a launch template for the Worker Nodes with the following:
    - AMI with Python 3 and required dependencies pre-installed.
    - Bootstrap script to configure the instance and start the Nodes.
    - IAM role with permissions for SQS, RDS, and S3.

2. Scaling Policies:

    - Add the appropriate scaling policies

3. Monitoring:

    - Use CloudWatch to monitor the scaling activity.

***

## Testing and Debugging
### End-to-End Testing
1. Submit a seed URL via the Client Node.
2. Verify that the URL is processed by the Master Node and crawled by the Crawler Nodes.
3. Check that the crawled data is stored in S3 and indexed in RDS.
4. Submit a search query and verify that results are returned from the SearchResponseQueue.

### Debugging Tips
- Use AWS CloudWatch to monitor SQS queues and RDS performance.
- Check logs for each node:
    - Client Node: Flask logs.
    - Master Node: Console output.
    - Crawler Nodes: Scrapy logs.
    - Indexer Node: Console output.

***
## Data Flow Diagram

![Data Flow Diagram](/.images/DataFlow.png)
