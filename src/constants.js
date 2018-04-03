export const MANAGE_ASSIGNMENT_PERMISSIONS = Object.freeze([
    'can_edit_assignment_info',
    'can_assign_graders',
    'can_edit_cgignore',
    'can_grade_work',
    'can_update_grader_status',
    'can_use_linter',
    'can_update_course_notifications',
    'manage_rubrics',
    'can_upload_bb_zip',
    'can_submit_others_work',
]);

export const MANAGE_GENERAL_COURSE_PERMISSIONS = Object.freeze([
    'can_edit_course_users',
    'can_edit_course_roles',
]);

export const MANAGE_COURSE_PERMISSIONS = Object.freeze([
    ...MANAGE_ASSIGNMENT_PERMISSIONS,
    ...MANAGE_GENERAL_COURSE_PERMISSIONS,
]);

export const MANAGE_SITE_PERIMSSIONS = Object.freeze([
    'can_manage_site_users',
]);
