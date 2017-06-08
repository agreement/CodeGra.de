# API
This is they API documentation for API verion 1 of the codebuil.de website.

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
right, so the URL `/api/v1/schools/23/teachers/3/children` should return all
children of the teacher with id 3 of the school with id 23. Last but the last
collection should have a id specifier when using nested collections, this means
the pattern `(collection/id)*/collection(/id)?` should always be used. For
example the URL `/api/v1/schools/teachers` is always illegal.

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
- **200**: Everything is went file and the server should return a useful result.
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
