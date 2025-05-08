# Distributed-Web-Crawling-and-Indexing-System-using-Cloud-Computing
## CSE354 - Distributed Computing Course Project
## Team Members
> - Mohamed Salah
> - Salma Hisham
> - Youssef Tamer
> - Salma Youssef

-----

## Overview

This project implements a distributed web crawling and indexing system using cloud computing services. The system is designed to efficiently crawl web pages, extract metadata, and store the results in a scalable and searchable format. It leverages AWS services such as SQS, RDS, and S3 for communication, storage, and processing. The system is modularized into smaller components for better maintainability.

----

## System Architecture
The system consists of the following components:

1. Client Node: 
   - Provides a Flask-based interface for submitting seed URLs and search queries.
    - Monitors the status of nodes, including:
        - **Instance Information**: Displays details such as `instanceId`, `cpuUsage`, `publicIp`, `storageUsage`, and `status` for each node.
        - **Critical Status**: Highlights nodes with critical conditions, including `nodeName`, `cpuUsage`, `storageUsage`, `status`, and any associated alerts.
    - Communicates with the Master Node through the `Client_Master_Queue`.
    - Displays search results retrieved from the `SearchResponseQueue`.
2. Master Node:
    - Manages the distribution of crawling tasks to Crawler Nodes.
    - Sends tasks to the queue `TaskQueue` for Crawler Nodes to process.
    - Interacts with an RDS database to store and update the status of URLs.
    - Ensures that duplicate URLs are not processed.
    - Tracks the health of worker nodes (Crawler and Indexer Nodes) using heartbeat messages.
3. Crawler Nodes:
    - Perform web crawling and extract metadata (e.g., title, description, keywords).
    - Store crawled HTML files in S3.
    - Send crawled urls to Indexer nodes through a queue `ResultQueue` to index them.
    - Send periodic heartbeat messages to their status queue `Crawler_Status`, including their IP address and the last crawled URL.
4. Indexer Nodes: 
    - Process crawled data retrieved from the Crawler Nodes through the queue `ResultQueue`.
    - Index the data using the Whoosh library, applying stemming, analysing keywords and cleaning text before storing it in the Whoosh index and RDS.
    - Handle search queries from the Client recieved thourgh `SearchQueue` and return results to the `SearchResponseQueue` for the Client to display.
    - Send periodic heartbeat messages to the `IndexerStatusQueue`, including their IP address and the last indexed URL.
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

1. Client node:
```bash
pip install boto3 flask flask-cors 
```
2. Crawler nodes:
```bash
pip install boto3 scrapy 
```
3. Indexer nodes
```bash
pip install boto3 pymysql scrapy nltk whoosh psutil
python3 -m nltk.downloader punkt punkt_tab stopwords
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
```bash
python Client_Backend.py 
```
Alternatively, Deploy it as a systemd service:

- Example service template:

```bash
[Unit]
Description=Backend Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=<working dir here>
ExecStart=/usr/bin/python3 <backend file to be run>
Restart=always

[Install]
WantedBy=multi-user.target

```
- Then enable and start this service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable indexer.service
sudo systemctl start indexer.service
```
2. Access the client interface via the public IP of the server:
> http://<PUBLIC_IP>:5000
3. Features available in the client interface:
    - ** Submit Seed URL **: Enter a seed URL, restricted domains, crawl depth, and page limit to initiate crawling.
    - ** Submit Search Query **: Enter keywords to search the indexed data.
    - ** Monitor Nodes **:
        - ** Instance Information **: View real-time details of nodes, including instanceId, cpuUsage, publicIp, storageUsage, and status.
        - ** Critical Status **: Identify nodes with critical conditions, including high CPU or storage usage, and view associated alerts.

**Master Node**
1. Start the Master Node script:
```bash
 python master.py
```
2. Monitor the `Client_Master_Queue` for incoming tasks.

3. Check logs for task distribution and heartbeat monitoring.

**Crawler Nodes**
1. Start the crawler script
```bash
 python crawling_spider.py
```
2. Ensure the crawler retrieves tasks from the TaskQueue and uploads results to S3.

3. Monitor the `Crawler_Status` queue for heartbeat messages to ensure the node is active.

**Indexer Node**
1. Start the indexer script

```bash
 python main.py
```

Alternatively, Deploy the Worker Nodes as a systemd service using steps listed in client node.

2. In our code we set the RDS password as a environment variable to avoid hardcoding it, so it could be set on the instance itself :
```bash
export RDS_PASSWORD=<your_rds_password>
```
 Alternatively, add it to the systemd service file.
 ```bash
Environment="RDS_PASSWORD=<your_rds_password>"
 ```

3. Monitor the ResultQueue and SearchQueue for messages.

4. Check the `IndexerStatusQueue` for heartbeat messages to ensure the node is active.

***

## Autoscaling 
1. Launch Template:
- Create a launch template for the Worker Nodes with the following:
    - AMI with Python 3 and required dependencies pre-installed.
    - Bootstrap script to configure the instance and start the Nodes.
    - IAM role with permissions for SQS, RDS, and S3.

2. Scaling Policies:

    - Add the appropriate scaling policies
    - As an example our system uses CloudWatch metrics (e.g., SQS queue length) to trigger autoscaling events., where Worker Nodes (Crawler and Indexer Nodes) are scaled up or down based on the number of pending tasks in the queues.

3. Monitoring:

    - Use CloudWatch to monitor the scaling activity.

### notes
- Fault Tolerance: Heartbeat monitoring implemented in our code ensures that failed nodes are detected and replaced automatically.
***

## Testing and Debugging
### End-to-End Testing
1. Submit a seed URL via the Client Node.
2. Verify that the URL is processed by the Master Node and crawled by the Crawler Nodes.
3. Check that the crawled data is stored in S3 and indexed in RDS.
4. Submit a search query and verify that results are returned from the SearchResponseQueue.
5. **Monitor Nodes**:
    - Verify that the **Instance Information** table displays the correct details for each node.
    - Check the **Critical Status** table for any nodes with high CPU or storage usage and ensure alerts are displayed correctly.

### Debugging Tips
- Use AWS CloudWatch to monitor SQS queues and RDS performance.
- Check status queues for heartbeat messages to ensure all nodes are active and reporting their status.
- Check logs for each node:
    - Client Node: Flask logs.
    - Master Node: Console output.
    - Crawler Nodes: Scrapy logs.
    - Indexer Node: Console output.


## Data Flow Overview
1. **Seed URLs**:
    - The Client Node sends seed URLs to the Master Node via the `Client_Master_Queue`.
    - The Master Node distributes these URLs to Crawler Nodes via the `TaskQueue`.

2. **Crawling**:
    - Crawler Nodes fetch the web pages, extract metadata, and store the HTML files in S3.
    - The crawled data is sent to the `ResultQueue`.
    - Periodically sends hearbeat messages to the `Client_Status` queue.

3. **Indexing**:
    - Indexer Nodes process the crawled data from the `ResultQueue`, index it using Whoosh, and store it in RDS.

4. **Search**:
    - The Client Node sends search queries to the `SearchQueue`.
    - Indexer Nodes process the queries and return results to the `SearchResponseQueue`.
    - Periodically sends hearbeat messages to the `IndexerStatusQueue` queue.

<!-- *** -->
<!-- ## Data Flow Diagram

![Data Flow Diagram](/.images/DataFlow.png) -->
