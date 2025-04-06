# This script creates an S3 bucket for a static website, uploads the website files to the bucket
# and sets up a CloudFront distribution to serve the website.
# It also configures the bucket policy to allow public access to the files.
# The website files should be placed in the './www' directory relative to this script.

import os
import mimetypes
import pulumi
import pulumi_aws as aws

# Create an S3 bucket for the website
statis_website_bucket = aws.s3.Bucket("color-challenge-website-bucket",
    website=aws.s3.BucketWebsiteArgs(
        index_document="index.html",
    ))

# Bucket policy to allow public access to the website files
public_access_block = aws.s3.BucketPublicAccessBlock('color-challenge-bucket-public-access-block',
    bucket=statis_website_bucket.id,
    block_public_acls=False,
    ignore_public_acls=False,
    block_public_policy=False,
    restrict_public_buckets=False
)

# Bucket policy to allow public read access to the bucket
# Note: This is a simplified policy. In production, consider using more restrictive policies.
bucket_policy = aws.s3.BucketPolicy("bucket-policy",
    bucket=statis_website_bucket.id,
    policy=statis_website_bucket.id.apply(
        lambda id: f"""{{
            "Version": "2012-10-17",
            "Statement": [{{
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": ["arn:aws:s3:::{id}/*"]
            }}]
        }}"""
    ))


# Function to upload files and directories to S3
def upload_directory(directory_path, parent_path=""):
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            upload_directory(item_path, os.path.join(parent_path, item))
        else:
            # Get the content type of the file
            file_path = os.path.join(parent_path, item)
            content_type = mimetypes.guess_type(item_path)[0] or "application/octet-stream"

            aws.s3.BucketObject(
                file_path.replace("\\", "/"),
                bucket=statis_website_bucket.id,
                key=file_path.replace("\\", "/"),
                source=pulumi.FileAsset(item_path),
                content_type=content_type
            )

# Upload the website files to the S3 bucket
website_dir = "./www"
if os.path.exists(website_dir):
    upload_directory(website_dir)
else:
    print(f"Error: Website directory {website_dir} does not exist")

# Create a CloudFront distribution for the S3 bucket
cdn = aws.cloudfront.Distribution("website-cdn",
    enabled=True,
    origins=[aws.cloudfront.DistributionOriginArgs(
        origin_id=statis_website_bucket.arn,
        domain_name=statis_website_bucket.website_endpoint,
        custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
            http_port=80,
            https_port=443,
            origin_protocol_policy="http-only",
            origin_ssl_protocols=["TLSv1.2"],
        ),
    )],
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        target_origin_id=statis_website_bucket.arn,
        viewer_protocol_policy="redirect-to-https",
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        cached_methods=["GET", "HEAD", "OPTIONS"],
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none",
            ),
        ),
        min_ttl=0,
        default_ttl=3600,
        max_ttl=86400,
    ),
    price_class="PriceClass_100",
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
        ),
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    ))

# Export the Bucket Name, website URL and CDN URL
pulumi.export("bucket_name", statis_website_bucket.id)
pulumi.export("website_url", statis_website_bucket.website_endpoint)
pulumi.export("cdn_url", cdn.domain_name)

# END OF FILE
# This script creates an S3 bucket for a static website, uploads the website files to the bucket
# and sets up a CloudFront distribution to serve the website. 
# It also configures the bucket policy to allow public access to the files.
# The website files should be placed in the './www' directory relative to this script.