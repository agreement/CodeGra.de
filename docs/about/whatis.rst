What is CodeGra.de?
====================
CodeGra.de is a blended learning application designed especially for programming
education. It makes grading and handing in programming exercises more insightful
and effective for students and more efficient for teachers, by providing an
online environment carefully designed to specifically suit the needs of modern
programming education.

Where programming exercises are currently reviewed in a classical and
counter-intuitive way, resulting in only little and vague feedback, CodeGra.de
creates the missing intuitive environment for reviewing programming exercises.

This is achieved using some of the key-features CodeGra.de provides:
- Line by line feedback making it possible to specifically write feedback for a
specific part of the code.
- Easy to use rubrics to aid consistent and prompt grading of assignments.
- CodeGra.de Filesystem enabling both students and teachers to access and hand
in files on the CodeGra.de system locally without any (website) overhead.
- CodeGra.de editor plugins allowing the teacher to locally review programming
assignments and fill in rubrics using the editor of choice.
- An online environment carefully designed to suit the needs of modern programming
education, with a wide variety of useful features.

This is all combined in an online environment that seamlessly integrates in
modern a LMS (e.g. `Canvas <https://www.canvaslms.com/>`_) using the LTI framework. Making
CodeGra.de both useful as standalone application and as integration in your
favourite LMS.

CodeGra.de Filesystem
----------------------
The CodeGra.de filesystem (or CodeGra.fs) can be used to mount a local
CodeGra.de instance on your computer to browse the assignments and files on the
server. The filesystem can be used for students to locally work on the
CodeGra.de mount and thus automatically hand in the assignment with each save.
For teachers the filesystem can be used to grade work without any overhead
locally using a preferred editor.

More information on installing and using the CodeGra.de filesystem can be found
in this documentation. The Github repository of the Filesystem can be
found on https://github.com/CodeGra-de/CodeGra.fs.

CodeGra.de Editor Plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^
Accompanying the CodeGra.de filesystem are the editor plugins. These plugins
allow for easy and intuitive grading of work locally in your favourite editor.
By using the combination of the filesystem and an editor plugin, overhead during
grading can be reduced to a bare minimum and all focus can be on the actual
grading of the work.

As of writing, there are editor plugins for the following editors:

* Vim (*CodeGra.vim*)
* Atom (*CodeGra.atom*)
* Emacs (*CodeGra.el*)

More information on the usage and installation of the specific plugins can be
found in this documentation.
