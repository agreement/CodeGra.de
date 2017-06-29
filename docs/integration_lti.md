Integration with LTI is not completely intuitive. In this document we try to describe the special cases where the integration doesn't work as you would expect. When LTI is activated these things change:

- In general LTI takes precedence. Everything get's created via LTI (courses/assignments/TA's/deadlines etc.). You can only change these details via LTI.
- To update/change details of an assignment an LTI launch request needs to be fired. This only happens when an assignment is accessed from the LTI provider. So when the teacher has updated for example the deadline, (s)he should open the assignment to update the details on codegra.de
- In our system an assignment has 3 states (hidden/open/done). When LTI is integrated the hidden and open state are managed by LTI.
- Only when the assignment is done, all grades are sent back to LTI.
- You can't upload blackboard .zip files.
