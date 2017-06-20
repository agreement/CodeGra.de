# API
This is the API documentation for API verion 1 of the codebuil.de website.

## General rules
### URL buildup
All API URL's should prefix `/api/v$x` where `$x` is the current version of the
API, which is 1 at the moment of writing. After this prefix the first comes the
first *collection*, a collection is a set of objects of something. Examples are
schools, a set of multiple schools, feedback, a set of feedback, or users, the
set of multiple users. All collections should always be plural nouns. When doing
a request to the collection this should apply to all items in this collection,
when allowed, filters can be used and should be passed as `GET` parameters.

However when querying a single object, always identified by id, this id should
be a new path in the URL. So querying a single school should use the url
`/api/v1/schools/1`.

Collections can be nested, so multiple collections in a single URL, however
these rules should be followed. First a single directory in the URL should
always contain only one collection. Second the URL should be read from left to
right, so the URL `/api/v1/schools/23/teachers/3/children/` should return all
children of the teacher with id 3 of the school with id 23 (please not the
required trailing slash). All but the last collection should have an id
specifier when using nested collections, this means the pattern
`(collection/id)*/collection/(id)?` (please note that there is **no** trailing
slash after an id) should always be used. For example the URL
`/api/v1/schools/teachers/` is always illegal.

To sort, filter and search `GET` parameters should be passed (see the next
section for Http methods documentation), it should follow the `key=value` where
the key should be generic, `category` instead of `school_category`. A special
case is the key `sort`, where there can be multiple options (separated by
spaces) (these are the different sort options) and each value should be
prepended with either a `-` or a `+` meaning respectively sort descending and
sort ascending.

### Http methods

Http methods should be used as the verb that can not be used in the URL. The
possible http methods are:

- **GET**: This method should be used to get something from the server. It
  should not have any side effects, so it should not alter the database for
  example.
- **POST**: This method should create a new object within the given collection.
  Once again the URL is used for filtering, for example a `POST` to
  `/api/v1/schools/5/teacher` should create a new teacher in the school with
  id 5. The content type should be `application/json` and the payload should be
  a valid JSON object.
- **PUT**: This method should be used to update an existing object or create the
  object if it does not exist. Filtering should be done using the URL (please
  note that `/api/v1/schools/5/teacher` is not valid as this is not a single
  object), the content type `application/json` and the payload should be a valid
  JSON object.
- **DELETE**: This method should be used to delete a object. The same rules
  apply as for the **PUT** method.
- **PATCH**: This method is the same as the **PUT** method, however it will
  **NOT** create a new object if the object does not exist.

Other Http methods may **NOT** be used.

### API responses
#### Http status codes
Http status codes should be used to convey the status of the request. The entire
list of status codes can be found online. However these are the most important
ones:
- **200**: Everything went OK and the server should return a useful result.
- **201**: This status should be used when a new resource is created after a
  POST, PUT request.
- **204**: This status should be used if the request was correct but no content
  should be returned.
- **400**: Should be signaled when a request was invalid.
- **401**: Should be used when the user is not authorized, so if the user is not
  logged in.
- **403**: Should be used when the user is logged in but the user is not
  authorized to see the requested object(s).
- **404**: Should be used when the requested object does not exist.
- **410**: Should be used if the object is no longer available.

#### Response
The response of the server should always be a valid JSON object, unless the
status code is 204, in this case there should not be a response at all.

This means that even if the status code is not 2xx (so not success), there
should be a response. In this case the response should be a JSON object with
at least the following keys:
- **message**: A short message that is somewhat useful for a non technical user.
- **description**: A technical error message that is somewhat useful for
  debugging purposes (please note that you should **NOT** send sensitive
  information).
- **code**: The error code that should uniquely identify the error.

A error message may be nested, where the nested errors should be in an array
behind the key `errors` and every item in the array should be a valid JSON error
with the above specified required keys.

### API documentation
Every API end point for every http method should be documented. The headline
structure should follow that of the URL but in reverse. So the API end
`/api/v1/schools/3/teachers` should be documented under the title Teachers,
ander **under** teachers there should be a subsection *schools*. Furthermore
every API call should have input object, with types for every key and
description, and an example output object. Last every API call should have a
higher level description of the use and working.

## Assignments
### Getting an assignment
#### HTTP Request
`GET http://example.com/api/v1/assignments/<ID>`

### Listing all assignments

```python
import requests

# As logged in user
requests.get('/api/v1/assignments/')
```

> The above code returns JSON structured like this with a status code of 200:
```json
[
  {
    "id": 1,
    "name": "Security",
    "course_name": "Besturingssystemen",
    "course_id": 1
  },
  {
    "id": 2,
    "name": "Shell",
    "course_name": "Besturingssystemen",
    "course_id": 1
  },
  {
    "id": 3,
    "name": "Final deadline",
    "course_name": "Project Software Engineering",
    "course_id": 2
  }
]
```

Get all assignments that the current user can see.

###### HTTP Request
`GET http://example.com/api/v1/assignments/`

### Getting all users that can grade the assignment

```python
import requests

# As logged in user
requests.get('/api/v1/assignments/5/graders')
```

> The above code returns JSON structured like this with a status code of 200:
```json
[
  {
    "names_ids": [('Thomas Schaper', 2), ('Devin Hillenius', 3)],
  }
]
```

#### HTTP Request
`GET http://example.com/api/v1/assignments/<ID>/graders`

### Divide assignments over graders

##### HTTP Request
`PATCH http://example.com/api/v1/assignments/<ID>/divide`

##### Query Parameters
Parameter | Description
--------- | -----------
graders | List of user id's of graders to divide the submissions of this assignment over

## Code
### Get code
##### HTTP Request
`GET http://example.com/api/v1/code/<ID>`

## Comment
### Code
#### Put comment in code
##### HTTP Request
`PUT http://example.com/api/v1/code/<ID>/comments/<lineno>`
#### Remove comment in code
`DELETE http://example.com/api/v1/code/<ID>/comments/<lineno>`

## Directories
### Submission
#### Get directory contents

```python
import requests

params = {
  'file_id': 1
}
requests.get('https://example.com/api/submissions/1/files/', params=params)
```

> The above command returns JSON like below with a status code of 200:
```json
{
  "id": 1,
  "name": "rootdir"
  "entries": [
    {
      "id": 2,
      "name": "file1.txt"
    },
    {
      "id": 3,
      "name": "subdir"
      "entries": [
        {
          "id": 4,
          "name": "file2.txt."
        },
        {
          "id": 5,
          "name": "file3.txt"
        }
      ],
    },
  ],
}
```

##### HTTP Request
`GET http://example.com/api/v1/submissions/<ID>/files/`

##### Query Parameters
Parameter | Description
--------- | -----------
file_id | Optional parameter that can be used to show the contents of a specific directory in the work

## Submissions

### Get submission
##### HTTP Request
`GET /api/v1/submissions/<ID>`
### Patch submission
##### HTTP Request
`PATCH /api/v1/submissions/<ID>`

### Assignment
#### Add new submission

```python
import requests
multipart_form_data = {
    'file1': open(myarchive, 'rb'),
    'file2': open('myfile.txt', 'rb'),
}

requests.post('https://example.com/api/v1/assignments/1/submission', files=multipart_form_data)
```

> The return code will be 204 and the body will be empty if the submission was added


###### HTTP Request
`POST http://example.com/api/v1/assignments/<ID>/submission`

###### Query Parameters
Parameter | Description
--------- | -----------
file* | A file that should be uploaded. It can be an archive which will be extracted. Multiple can be specified but all keys should start will `file`

#### Get all submissions

```python
import requests

requests.get('https://example.com/api/v1/assignments/1/submissions/')
```

> The above command returns JSON structured like below:
```json
[
  {
    "id": 1,
    "user_name": John Doe
    "user_id": 1,
    "grade": 6,
    "comment": "General feedback",
    "created_at": "13-01-2017 10:05",
  },
  ...
]
```

```python
import requests

params = {
  'csv' = 'filename.csv'
}

requests.get('https://example.com/api/v1/assignments/1/submissions/params=params')
```
> The above command will return a CSV file structured like below:
```
id,user.name,user_id,grade,comment,created_at
1,"John Doe",1,6,"General Feedback","13-01-2017 10:05"
...
```

###### HTTP Request
`GET http://example.com/api/v1/assignments/<ID>/submissions/`

###### Query Parameters
Parameter | Description
--------- | -----------
csv | Optional parameter that can be set to retrieve all submissions as a csv file


#### Import submissions from blackboard zip file

```python
import requests
multipart_form_data = {
    'file': open(bbzip, 'rb'),
}

requests.post('https://example.com/api/v1/assignments/1/submissions/', files=multipart_form_data)
```

> The return code will be 204 and the body will be empty if the submissions were added


###### HTTP Request
`POST http://example.com/api/v1/assignments/<ID>/submissions/`

###### Query Parameters
Parameter | Description
--------- | -----------
file | The file that will be uploaded and imported. This file must be a zip-archive containing a Blackboard Gradebook.


## User
### Login
#### Login a new user

```python
import requests

login_data = {
    'email': 'admin@example.com',
    'password': 'admin',
}

requests.post('https://example.com/api/v1/login', json=json_data)
```

> The return will a json as described below in the GET request

This endpoint will login a new user and return its information.

###### HTTP Request
`POST http://example.com/api/v1/login`

###### Query Parameters
Parameter | Description
--------- | -----------
email | The email of the user that should be logged in
password | The password of the user identified by the email

##### Get login credentials from a user

```python
import requests

requests.get('https://example.com/api/v1/login')
```

> The above command returns JSON structured like this with a status code of 200:
```json
{
  "id": 1,
  "name": "John Doe" ,
  "email": "John@example.com"
}
```

This endpoint will get the user information of the currently logged in user.

###### HTTP Request
`GET http://example.com/api/v1/login`

##### Logout a user

```
import requests

requests.post('https://example.com/api/v1/logout')
```

> This will return no data and a status code of 204

Logout the currently logged in user.

###### HTTP Request
<<<<<<< HEAD
`POST http://example.com/api/v1/logout`
=======
`POST http://example.com/api/v1/logout`

### Permissions
#### Getting all permissions
```python
import requests

# Logged in as a user
requests.get('/api/v1/permissions/')
```

> This will return JSON structured like this with a status code of 200:

```json
{
  "edit_name": true,
  "edit_email": true,
  "add_user": false,
}
```

Get all general or course permissions. Each item in the returned JSON object is
a permission and the value is if the logged in user has this permission.

<aside class="warning">
This API call is quite expensive on the server side. If you only need one
permission please specify the permission using the `GET` parameters. However if
you do need all permissions do not create multiple requests but simply get all.
</aside>

<aside class="notice">
If you want permissions for course that does not exist you will <b>NOT</b>
receive a 404 error, but simply that you do not have permissions for anything
for this course. However when getting a single permission you <b>WILL</b> get a
404 error when getting a permission that does not exist.
</aside>

##### HTTP Request
`GET https://example.com/api/v1/permissions/`

##### Query Parameters
| Parameter  | Description                                                                                                                               |
| ---------  | -----------                                                                                                                               |
| course_id  | The id of the course if you want course permissions, if not specified general permissions are returned.                                   |
| permission | The name of the specific permission you want. This changes the resulting JSON to a boolean indicating if you have this permission or not. |

## Assignments
### Listing all assignments

```python
import requests

# As logged in user
requests.get('/api/v1/assignments/')
```

> The above code returns JSON structured like this with a status code of 200:
```json
[
  {
    "id": 1,
    "name": "Security",
    "course_name": "Besturingssystemen",
    "course_id": 1
  },
  {
    "id": 2,
    "name": "Shell",
    "course_name": "Besturingssystemen",
    "course_id": 1
  },
  {
    "id": 3,
    "name": "Final deadline",
    "course_name": "Project Software Engineering",
    "course_id": 2
  }
]
```

Get all assignments that the current user can see.

###### HTTP Request
`GET http://example.com/api/v1/assignments/`

## Snippets
### Getting all snippets
```python
import requests

# Logged in as a user
requests.get('https://example.com/api/v1/snippets/')
```

> This will result in the following JSON object with status code of 200:
```json
{
    "malloc": {
      "id": 1,
      "value": "Don't forget to check malloc for return value."
    },
    "free" {
      "value": "Don't do a double free.",
      "id": 2
    }
}
```

Get all snippets for the current user in a large object where the keys are the
keys that should be used for the snippet.


<aside class="notice">
This is only valid for work when the current user has the `can_use_snippets`
permission.
</aside>

#### HTTP Request
`GET https://example.com/api/v1/snippets/`

### Deleting a snippet
```python
import requests

# Logged in as a user
requests.delete('https://example.com/api/v1/snippets/{}'.format(snippet_id))
```

> This will result in an empty response with status code 204

Delete the snippet with the specified id. Only snippets owned by the current
user can be deleted.

#### HTTP request
`DELETE https://example.com/api/v1/snippets/<ID>`

### Add or modify a snippet
```python
import requests

json_data = {"key": "fgets", "value": 'Fgets is niet veilig.'}

# Logged in as a user
requests.put('https://example.com/api/v1/snippet', json=json_data)
```

> This will return JSON structured like below with status code 201

```json
{
    "id": 1
}
```

Add a new snippet or modify an existing one. If the specified key is already a
snippet for the current user, the value of this snippet will be changed.

#### HTTP Request
`PUT https://example.com/api/v1/snippet`

#### Query Parameters
| Parameter | Description                                                       |
| --------- | -----------                                                       |
| key       | The key of the new or existing snippet                            |
| value     | The value of the new snippet or the new value of the old snippet. |

### Patch a snippet
```python
import requests

json_data = {"key": "fgets", "value": 'Fgets is niet veilig.'}

# Logged in as a user
requests.patch('https://example.com/api/v1/snippets/1', json=json_data)
```

> The return code will be 204 and the body will be empty

Updates the key and value of the snippet with the given id.

#### HTTP Request
`PATCH https://example.com/api/v1/snippets/<ID>`

#### Query Parameters
| Parameter | Description                                  |
| --------- | -----------                                  |
| key       | The current or updated key of the snippet.   |
| value     | The current or updatet value of the snippet. |
