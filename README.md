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
2. Master Node: Manages the distribution of crawling tasks to Crawler Nodes.
3. Crawler Nodes: Perform web crawling, extract metadata, and store results in S3.
4. Indexer Node: Processes crawled data, stores it in RDS, and handles search queries.

---

## Key Features
Distributed crawling with support for multiple nodes.
Metadata extraction and storage in AWS RDS.
Search functionality with results delivered via AWS SQS.
Scalable architecture leveraging AWS cloud services.

***

## Steps to Use
1. Prerequisites

AWS account with access to SQS, RDS, and S3.
Python 3.8+ installed on all nodes.
Required Python libraries installed:
``` pip install boto3 pymysql flask flask-cors scrapy ```

2. Setting Up AWS Resources

    1. Create SQS Queues:

        - Client_Master_Queue: For seed URLs.
        - SearchQueue: For search queries.
        - ResultQueue: For crawled data.
        - SearchResponseQueue: For search results.

    2. Set Up RDS:

        - Create an RDS instance with a database named new_schema.
        - Use the following schema for the indexed_data table:
                ``` 
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

    3. Create an S3 Bucket:

        - Store crawled HTML files in the bucket.

    4. Configure IAM Roles:

        - Ensure all nodes have the necessary permissions to access SQS, RDS, and S3.

3. Running the System

    **Client Node**
    1. Start the Flask server:
        ``` python Client_Backend.py ```
    2. Access the client interface via the public IP of the server:
    > http://<PUBLIC_IP>:5000
    3. Submit a seed URL and depth or a search query.

    **Master Node**
    1. Start the Master Node script:
    `` python master.py``
    2. Monitor the Client_Master_Queue for incoming tasks.

    **Crawler Nodes**
    1. Start the crawler script
    `` python crawling_spider.py``
    2. Ensure the crawler retrieves tasks from the TaskQueue and uploads results to S3.

    **Indexer Node**
    1. Start the indexer script
    `` python main.py``

       Alternatively, Deploy the Indexer Node as a systemd service:
    `` sudo systemctl start indexer.service``

    2. Monitor the ResultQueue and SearchQueue for messages.

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
    - Indexer Node: Systemd logs.

***
## Data Flow Diagram

![Data Flow Diagram](/.images/DataFlow.png)