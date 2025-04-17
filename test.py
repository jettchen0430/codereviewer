api_key = "sk-lrgdqnlbsafbgtmtivflkgorpzixnlwtzgbdlqvjosfzhuwv"
base_url = "https://api.siliconflow.cn/v1"
client_configs = {
    "api_version": "2023-03-15-preview",
    "api_type": "azure",
}
openai_async_client = create_openai_async_client(
    api_key=api_key, base_url=base_url, client_configs=client_configs
)
