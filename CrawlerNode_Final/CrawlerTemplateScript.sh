#!/bin/bash
sudo yum update -y
sudo yum install -y python3 python3-pip git
cd /home/ec2-user
aws s3 cp s3://s3nodescode/CrawlerNode_Final ./CrawlerNode_Final --recursive
sudo touch mainlog.txt
sudo chown ec2-user:ec2-user /home/ec2-user/mainlog.txt
cd CrawlerNode_Final/
pip3 install --upgrade pip
python3 -m venv venv
source venv/bin/activate
pip install scrapy
pip install boto3
pip install --no-cache-dir -r CrawlerReq.txt
python main.py
