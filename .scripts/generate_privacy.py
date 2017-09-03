#!/usr/bin/env python3

import mistune


TEMPLATE = """
<template>
    <div class="privacy-note">
        <div class="inner-privacy">
        {statement}
        </div>
        <h4>Software licenses</h4>
        <p>
            All software running this website is available under AGPL-v3, this
            means you have the right to see the source code (and many more).
            Contributions to CodeGra.de are very welcome, please checkout
            our <a href="https://github.com/CodeGra-de/CodeGra.de"
            target="__blank">github repo</a>, and don't forget to fork and
            star! </p>
        <small>&copy; {{{{ new Date().getFullYear() }}}} - CodeGra.de - Made
        with ❤️ &amp 🍺</small>
    </div>
</template>

<style lang="less" scoped>
.privacy-note {{
    p, .inner-privacy {{
        text-align: left;
    }}
    line-height: 1.25;

    h1, h2, h3, h4, h5, small {{
        text-align: center;
    }}

    ul {{
        margin-top: 1rem;
    }}
}}
</style>
""" [1:]

DEFAULT_STATEMENT = """
<h3>Privacy Notice</h3>
<p>
    This privacy notice discloses the privacy practices for CodeGra.de. This
    privacy notice applies solely to information collected by this website. It
    will notify you of the following:
</p>

<p>
    What personally identifiable information is collected from you through the
    website, how it is used and with whom it may be shared. What choices are
    available to you regarding the use of your data. The security procedures in
    place to protect the misuse of your information. How you can correct any
    inaccuracies in the information.
</p>

<h4>Information Collection, Use, and Sharing</h4>
<p>
    We are the sole owners of the information collected on this site. We only
    have access to/collect information that you voluntarily give us via email
    or using the website. We will not sell, rent this information to anyone. We
    will not share this information except for information that is necessary
    for grading, as doing grade passback to the used LMS.
</p>

<p>
    We will not contact you using email in the future, except for automatic
    emails that are necessary for features of the given service such as but not
    limited to the 'forgot password' functionality.
</p>

<h4>Your Access to and Control Over Information</h4>
<p>
    You may change any data you submit. You can do the following at any time by
    contacting us via the email address on our website:

    <ul>
        <li>See what data we have about you, if any.</li>
        <li>Change/correct any data we have about you.</li>
        <li>
            Express any concern you have about our use of your data.
        </li>
    </ul>

    We will however not change or delete any content related to your work but
    not created by you, such as but not limited to grades and feedback. Nor
    will we change submissions after the deadline without the conformation of a
    user that has permission to do so. We will also not give or change
    information about you that is not yet released to you for a course by a
    teacher.
</p>
""" [1:-1]


def get_statement():
    try:
        with open('PRIVACY_STATEMENT.md', 'r') as f:
            print('Using custom privacy statement')
            return mistune.markdown(f.read(), escape=False, hard_wrap=True)
    except FileNotFoundError:
        print('Using default privacy statement.')
        return DEFAULT_STATEMENT


def main():
    print('Writing privacy statement.')
    with open('src/components/PrivacyNote.vue', 'w') as f:
        f.write(TEMPLATE.format(statement=get_statement()))


main()
