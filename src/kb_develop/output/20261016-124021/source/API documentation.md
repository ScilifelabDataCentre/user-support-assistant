https://serve.scilifelab.se/docs/api-documentation/

This page describes how to use the API endpoints of SciLifeLab Serve to fetch information about the platform, lists of the public apps and models, and information about individual apps and models. To follow this guide you are expected to be comfortable with HTTP requests and JSON responses.

You can make an API request by simply opening a particular URL in your web browser or by using a terminal tool like [curl](https://curl.se/). In response, you will always receive a JSON formatted output.

## Basic API endpoints

### Health check

**GET** `https://serve.scilifelab.se/openapi/v1/are-you-there`

Simplest API endpoint useful for testing and verification. Returns "true" if system is up and running.

### System version

**GET** `https://serve.scilifelab.se/openapi/v1/system-version`

Returns the current version of SciLifeLab Serve. Response includes `system-version`, `build-date`, `image-tag`.

### API information

**GET** `https://serve.scilifelab.se/openapi/v1/api-info`

The Open API basic API information endpoint in accordance to the standard. Includes information about the latest API version.


## Fetching public apps and models

### List public apps and models

**GET** `https://serve.scilifelab.se/openapi/v1/public-apps`

**GET** `https://serve.scilifelab.se/openapi/v1/public-apps?limit=5`

This endpoint returns a list of apps and models that are publicly available (listed in the public app catalogue of SciLifeLab Serve). It returns a list of apps and models ordered by date created from the most recent to the oldest. If needed, you can limit the number of returned items by adding a `limit` filter as shown in the example above.

#### Returned fields (per app)

Each list item includes, at minimum:

- `id`
- `name`
- `url`
- `description`
- `created_on`
- `updated_on`
- `access`
- `k8s_user_app_status`
- `latest_user_action`
- `app_status`
- `app_type`
- `table_field.url` (will be depreciated in the next version of the API)

#### Example output

The response contains a `data` object with:

```json
{
  "data": [
    {
      "id": 123,
      "name": "Some Public App",
      "url": "https://…",
      "description": "…",
      "created_on": "2025-12-01T10:00:00Z",
      "updated_on": "2025-12-10T12:00:00Z",
      "access": "public",
      "latest_user_action": "…",
      "k8s_user_app_status": "Running",
      "app_status": "Running",
      "app_type": "Streamlit",
      "table_field": {"url": "https://…"}
    }
  ]
}
```

#### Errors

- HTTP 403 if `limit` is invalid.
- HTTP 500 if the system is unable to collect the list of public apps.

### Retrieve info about a single public app or model

**GET** `https://serve.scilifelab.se/openapi/v1/public-apps/<APP_ID>`

This endpoint retrieves information about a single public app or model. The requested URL needs to include the ID of the application in the SciLifeLab Serve database.

#### Returned fields

The response contains an `app` object with:

- `id`
- `name`
- `url`
- `description`
- `created_on`
- `updated_on`
- `access`
- `k8s_user_app_status`
- `app_status`
- `app_type`

#### Errors

The endpoint returns HTTP 404 in the following cases:

- No app exists with the given `APP_ID`.
- The app exists but is of an incorrect type.
- The app is not public.
- The app has been deleted.

If `APP_ID` is missing or less than 1, the API returns HTTP 403. 

Unexpected failures retrieving the app return HTTP 500.

## Content statistics

**GET** `https://serve.scilifelab.se/openapi/v1/content-stats`

This endpoint allows to get aggregated statistics about usage of SciLifeLab Serve.

#### Returned fields

- `stats_date_utz`  
- `stats_success`  
- `stats_message`  
- `stats_notes`  
- `n_active_projects`  
- `n_users`  
- `n_apps`
- `n_apps_public`  
- `apps_by_type`  
- `new_users_by_year`  
- `users_by_university`  
- `apps_by_image_registry`  

#### Errors

The returned value of `stats_success` indicates whether all statistic sub-queries succeeded. If statistics gathering fails, each error message is added to and displayed in the value of `stats_message`. 

Numeric counts default to '-1' if the related computation fails.
