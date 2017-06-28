[green list]: https://i.imgur.com/PUKtXtt.png "green list"
[orange pencil]: https://i.imgur.com/WCmqq4N.png "orange pencil"






Documentatie CodeGra.de
===

About
---

This project started out as a university project for the course Software Engineering at the the UvA (University of Amsterdam). Current grading tools focus on classic writing assignments. As computer science students (and teaching assistants) we noticed that a good piece of software for grading code, and recieving feedback, was lacking. Que CodeGrade. With CodeGrade one can grade code line by line, apply linters over the code, add feedback shortcuts, and much more all in an intuitive interface. CodeGrade is the first grading tool that started with code in mind. CodeGrade is also integrated with LTI in online learning environments such as Canvas or Blackboard.

Key Features
---
* line by line (inline) feedback
  ![](https://i.imgur.com/3yPRL3u.gif)
* linters
  ![](https://gitlab-fnwi.uva.nl/PSE1617B/pse1617b/blob/a9e65d60cc382bcf7e8695c2ab47cb6315777703/docs/manual_data/linter.ogv)
* integration with LTI (Canvas/Blackboard)
* feedback snippets


Pages
---


Workflows
---

- ### Student: ###
    When you log in as a student, you are automatically go to the assignments page. Here all the upcomming deadlines can be found. Three buttons allow you to toggle filters for the states an assignment an be in; submitting, grading, done. After you click on an assignment you can submit a file as well as see all previous submissions for that assignment. Also on this page you can view the rubric that will be used for grading (if a rubric is used). A Student can submit his/her assignments by uploading a single .tar.gz/.tar/.zip which contains the code, and maybe a PDF. If an assignment is labled 'done' a student can check his/her grade as well as read the given inline and general feedback. From the code viewer a student can download the submission and/or all given feedback.

- ### Teacher: ###
    The basic idea for teachers is that they, or teaching assistants can add assignments to existing courses and grade them once submitted by students. While grading you can click on individual lines of code and add direct inline feedback to them. From the courses page CodeGrade  lets you easily devide submissions ready for grading over all, or some, TA's by clicking on 'manage course'. From here you can click on the assignment and a dropdown menu will apear where you can determine which TA's you want do devinde between
 Devision is done randomly and assigned submissions can always be reassigned. In the previously mentioned drop down menu you can also run linters on all submissions. Linter errors will show up in the submissions as red linenumbers. ![](http://i.imgur.com/2kU11p2.png =300x).
    Once assigned a TA can switch between viewing all submissions and all submissions assigned to him or her. While grading an assignment, you switch to next or previous submission!!
 as well as select any submission from a dropdown menu. You can also return to the submission page. From here you can export the table with (graded) submissions as a csv file. A hand full of extra options are available for this feature -insert gif of export menu-.



F.A.Q
---
General questions:
- __How can I see all assignments for one course?__
  Search for the course on the _assignments_ page, or click in the top menu on _courses_, and then click on the green list button ![green list] to the right of a course.

Student questions:
- __How can I see my grade?__
  Find the assignment on the _assignments_ page. Click on the assignment. If the assignment is graded one can see their grade now.


TA questions:
- __How do I access a courses management page?__
  Click on in the top menu on _courses_. From this page one can see all the courses they are enrolled in / can manage. To edit a course's details, click on the orange pencil ![orange pencil] on the right of the course name. Now you can see all the assignments of this course. Click an assignment to edit it's details.
- __How can I divide the submitted submissions for an assignment over the TA's?__
  Click in the top menu on _courses_. Click on the orange pencil ![orange pencil] to the right of a course. Click on an assignment. Here one can edit all the details of an assignment.
- __How can I run a linter over all submitted submissions for an assignment?__
  Click in the top menu on _courses. Click on the orange pencil ![orange pencil] to the right of a course. Click on an assignment. Here one can edit all the details of an assignment.
