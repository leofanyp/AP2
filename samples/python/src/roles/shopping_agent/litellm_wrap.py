import os
import litellm
import logging
from litellm import CustomLLM, completion, get_llm_provider
from litellm.types.utils import ModelResponse
from azure.identity import CertificateCredential

# ==========================================================================================
#   Checkout use case access settings
# ==========================================================================================
os.environ["AZURE_OPENAI_STREAM_WITH_LANGCHAIN"] = 'NO'
os.environ['AZURE_OPENAI_ENDPOINT'] = "https://llm-multitenancy-exp.jpmchase.net/ver2/"

os.environ['AZURE_TENANT_ID'] = "79C738E8-25CD-4C36-ADF6-6EA2ED78F6A4"

# Checkout access info from FID: K029409
# Ask tech lead for these values
#os.environ['AZURE_SPN_CLIENT_ID']               # e.g. 8d27ef15-xxxx-xxxx-xxxx-f6f86b5c222a
#os.environ['AZURE_OPENAI_API_KEY']
CERTIFICATE_PATH = "./.venv/checkout-dev.jpmchase.net.txt.cer"  # Change the path to where your certificate is stored
CERTIFICATE_PATH = "/Users/I793486/projects/llm/smartsdk/checkout-dev.jpmchase.net.txt.cer"


# OpenAI model info
os.environ['AZURE_OPENAI_API_VERSION'] = "2024-12-01-preview"
os.environ['AZURE_OPENAI_MODEL'] = "o3-mini-2025-01-31"
#os.environ['AZURE_OPENAI_MODEL'] = 'gpt-4-0613' # Replace 'gpt-4-0613' with desired deployment_id. Ensure base_url entered contains desired deployment.
os.environ['AZURE_OPENAI_O1_MODEL'] = "o3-mini-2025-01-31"


# Working one!
os.environ['AZURE_OPENAI_API_VERSION'] = "2024-12-01-preview"
os.environ['AZURE_OPENAI_MODEL'] = "gpt-5-mini-2025-08-07"


# Set your Azure environment variables
#os.environ["AZURE_API_KEY"] = "your-azure-api-key"
#os.environ["AZURE_API_BASE"] = "https://your-openai-resource.openai.azure.com/"
#os.environ["AZURE_API_VERSION"] = "2023-07-01-preview" # or your specific version



# ==========================================================================================
#                                Set proxy
# ==========================================================================================
os.environ["http_proxy"] = "proxy.jpmchase.net:10443"
os.environ["https_proxy"] = "proxy.jpmchase.net:10443"
if 'no_proxy' in os.environ:
    os.environ["no_proxy"] = os.environ["no_proxy"] + ",jpmchase.net" + ",openai.azure.com"
else:
    os.environ["no_proxy"] = 'localhost,127.0.0.1,jpmchase.net,openai.azure.com'


# ==========================================================================================
#                        Get OpenAI Access Token using SPN
# ==========================================================================================

def get_access_token():
    # to fecth cert from local file
    #dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    #print(f'DIR PATH : {dir_path}')
    #cert_path = dir_path + "/cert/apim-exp.pem"

    # get access token
    scope = "https://cognitiveservices.azure.com/.default"
    logging.info("Getting ACCESS_TOKEN %s", scope)
    credential = CertificateCredential(
        client_id=os.environ["AZURE_SPN_CLIENT_ID"],
        certificate_path= CERTIFICATE_PATH,  #cert_path,
        #certificate_password="password",  # only for use with .pfx file types instead of a .pem
        tenant_id=os.environ["AZURE_TENANT_ID"],
        scope=scope,
        logging_enable=True
    )

    get_token_reps = credential.get_token(scope)
    logging.info("get_token_reps, %s", get_token_reps)

    access_token = get_token_reps.token
    logging.info("===ACCESS_TOKEN:===" + access_token +'\n')
    return access_token


# Define the custom model wrapper
class MyCustomAzureLLM(CustomLLM):
    """
    A custom LiteLLM model that wraps Azure OpenAI and customizes the request.
    """
    def __init__(self):
        super().__init__()
        self.underlying_model = "azure/your-deployment-name" # The real Azure model name

        logging.info('Using Azure OPENAI with an o* Model')
        self.access_token = get_access_token()
        # client = AzureOpenAI(
        #     # Please note: you can insert the API key as a python variable, or include it in the headers manually using 'api-key' as the key
        #     api_key=os.environ["AZURE_OPENAI_API_KEY"],
        #     azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        #     api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        #     default_headers={
        #         "Authorization": f"Bearer {access_token}",
        #         "user_sid": "REPLACE",
        #         # "api-key": os.environ["AZURE_OPENAI_API_KEY"]
        #     }
        # )


    def completion(self, *args, **kwargs) -> ModelResponse:
        """
        Customizes the request before calling the underlying Azure model.
        """
        # # --- Start customization logic ---
        # messages = kwargs.get("messages", [])

        # # Add a custom system message to the beginning of the message list
        # custom_system_message = {
        #     "role": "system",
        #     "content": "You are a helpful and polite assistant. Always respond with a positive and friendly tone."
        # }

        # # Insert the system message if it's not already present
        # if not messages or messages[0].get("role") != "system":
        #     messages.insert(0, custom_system_message)

        # kwargs["messages"] = messages
        # --- End customization logic ---

        print("Sending customized request to Azure with messages:")
        print("kwargs: ", kwargs)

        kwargs["model"] = "azure/" + os.environ["AZURE_OPENAI_MODEL"]
        kwargs["api_base"] = os.environ["AZURE_OPENAI_ENDPOINT"]                                   # azure api base
        kwargs["api_version"] = os.environ["AZURE_OPENAI_API_VERSION"]                                   # azure api version
        kwargs["api_key"] = os.environ["AZURE_OPENAI_API_KEY"]                                       # azure api key
        print("kwargs: ", kwargs)

        return litellm.completion(
            #model = "azure/" + os.environ["AZURE_OPENAI_MODEL"],             # model = azure/<your deployment name>
            #api_base = os.environ["AZURE_OPENAI_ENDPOINT"],                                      # azure api base
            #api_version = os.environ["AZURE_OPENAI_API_VERSION"],                                   # azure api version
            #api_key = os.environ["AZURE_OPENAI_API_KEY"],                                       # azure api key
            #messages = [{"role": "user", "content": "good morning"}],
            temperature = 1,
            extra_headers={
                "Authorization": f"Bearer {self.access_token}",
                "user_sid": "REPLACE"
            },
            *args, **kwargs
        )
        # Call the standard LiteLLM completion with the modified arguments
        #return litellm.completion(model=self.underlying_model, *args, **kwargs)

    async def acompletion(self, *args, **kwargs) -> ModelResponse:
        """
        Customizes the request for asynchronous calls.
        """
        # # --- Start customization logic (similar to above) ---
        # messages = kwargs.get("messages", [])
        # custom_system_message = {
        #     "role": "system",
        #     "content": "You are a helpful and polite assistant. Always respond with a positive and friendly tone."
        # }
        # if not messages or messages[0].get("role") != "system":
        #     messages.insert(0, custom_system_message)
        # kwargs["messages"] = messages
        # --- End customization logic ---

        print("Sending customized async request to Azure with messages:")
        print(kwargs["messages"])
        #kwargs = self.setup_kwargs(kwargs)
        kwargs["model"] = "azure/" + os.environ["AZURE_OPENAI_MODEL"]
        kwargs["api_base"] = os.environ["AZURE_OPENAI_ENDPOINT"]                                   # azure api base
        kwargs["api_version"] = os.environ["AZURE_OPENAI_API_VERSION"]                                   # azure api version
        kwargs["api_key"] = os.environ["AZURE_OPENAI_API_KEY"]                                       # azure api key
        print("kwargs: ", kwargs)

        return await litellm.acompletion(
            #model = "azure/" + os.environ["AZURE_OPENAI_MODEL"],             # model = azure/<your deployment name>
            #api_base = os.environ["AZURE_OPENAI_ENDPOINT"],                                      # azure api base
            #api_version = os.environ["AZURE_OPENAI_API_VERSION"],                                   # azure api version
            #api_key = os.environ["AZURE_OPENAI_API_KEY"],                                       # azure api key
            #messages = [{"role": "user", "content": "good morning"}],
            temperature = 1,
            extra_headers={
                "Authorization": f"Bearer {self.access_token}",
                "user_sid": "REPLACE"
            },
            *args, **kwargs
        )
        #return await litellm.acompletion(model=self.underlying_model, *args, **kwargs)


logging.basicConfig(level=logging.DEBUG)


# Register the custom model with LiteLLM
# Make sure this is imported and run before the ADK agent is defined.
my_custom_llm = MyCustomAzureLLM()
litellm.custom_provider_map = [
    {"provider": "my-custom-google", "custom_handler": my_custom_llm}
]

if __name__ == "__main__":
    # resp = my_custom_llm.completion(messages = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     #{"role": "assistant", "content": "Please explain about Quantum computing."},
    #     {"role": "assistant", "content": "Just a test."},
    # ])

    # #resp = my_custom_llm.completion(messages = [{"role": "user", "content": "good morning"}])
    # print("Custom model response: ", resp)

    import asyncio
    resp = asyncio.run( my_custom_llm.acompletion(messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        #{"role": "assistant", "content": "Please explain about Quantum computing."},
        {"role": "assistant", "content": "Just a test."},
    ]))
    print("Custom model response: ", resp)
