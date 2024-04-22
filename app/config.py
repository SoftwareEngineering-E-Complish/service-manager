# URLs
INVENTORY_SERVICE_URL = "inventory-service"
LLM_SERVICE_URL = "llm-service:8888"
USER_SERVICE_URL = "user-manager:8080"
IMAGE_SERVICE_URL = "image-service:8080"
GEOLOCATION_API_URL = "https://us1.locationiq.com/v1/search"

# Endpoint templates
QUERY_SCHEMA_ENDPOINT_TEMPLATE = "http://{}/schema/propertyQuery"
PROPERTY_QUERY_ENDPOINT_TEMPLATE = "http://{}/queryProperties"
PROPERTIES_BY_USER_ENDPOINT_TEMPLATE = "http://{}/fetchPropertiesByUser"
LLM_QUERY_ENDPOINT_TEMPLATE = "http://{}/generates/query"
TOKEN_VERIFICATION_ENDPOINT_TEMPLATE = "http://{}/verifyAccessToken"
USER_ID_ENDPOINT_TEMPLATE = "http://{}/userId"
UPLOAD_IMAGE_ENDPOINT_TEMPLATE = "http://{}/upload"
PRIMARY_IMAGE_ENDPOINT_TEMPLATE = "http://{}/getPrimaryImageUrl"
ALL_IMAGES_ENDPOINT_TEMPLATE = "http://{}/getImageUrls"

# Endpoints
QUERY_SCHEMA_ENDPOINT = QUERY_SCHEMA_ENDPOINT_TEMPLATE.format(INVENTORY_SERVICE_URL)
PROPERTIES_BY_USER_ENDPOINT = PROPERTIES_BY_USER_ENDPOINT_TEMPLATE.format(INVENTORY_SERVICE_URL)
PROPERTY_QUERY_ENDPOINT = PROPERTY_QUERY_ENDPOINT_TEMPLATE.format(INVENTORY_SERVICE_URL)
LLM_QUERY_ENDPOINT = LLM_QUERY_ENDPOINT_TEMPLATE.format(LLM_SERVICE_URL)
TOKEN_VERIFICATION_ENDPOINT = TOKEN_VERIFICATION_ENDPOINT_TEMPLATE.format(USER_SERVICE_URL)
USER_ID_ENDPOINT = USER_ID_ENDPOINT_TEMPLATE.format(USER_SERVICE_URL)
UPLOAD_IMAGE_ENDPOINT = UPLOAD_IMAGE_ENDPOINT_TEMPLATE.format(IMAGE_SERVICE_URL)
PRIMARY_IMAGE_ENDPOINT = PRIMARY_IMAGE_ENDPOINT_TEMPLATE.format(IMAGE_SERVICE_URL)
ALL_IMAGES_ENDPOINT = ALL_IMAGES_ENDPOINT_TEMPLATE.format(IMAGE_SERVICE_URL)
