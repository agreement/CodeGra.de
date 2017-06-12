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

## Works
### Assignment
#### Add new work

```python
import requests
multipart_form_data = {
    'file1': open(myarchive, 'rb'),
    'file2': open('myfile.txt', 'rb'),
}

requests.post('https://example.com/api/v1/assignments/1/work', work=multipart_form_data)
```

> The return code will be 204 and the body will be empty if the work was added


###### HTTP Request
`POST http://example.com/api/v1/assignments/<ID>/work`

###### Query Parameters
Parameter | Description
--------- | -----------
file* | A file that should be uploaded. It can be an archive which will be
extracted. Multiple can be specified but all keys should start will `file`

## User
### Login
#### Login a new user

```python
import requests

login_data = {
    'email: 'admin@example.com',
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
`POST http://example.com/api/v1/logout`

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
