"""
Enrollment API for creating, updating, and deleting enrollments. Also provides access to enrollment information at a
course level, such as available course modes.

"""
from django.utils import importlib
import logging
from django.conf import settings

log = logging.getLogger(__name__)


class CourseEnrollmentError(Exception):
    """Generic Course Enrollment Error.

    Describes any error that may occur when reading or updating enrollment information for a user or a course.

    """
    def __init__(self, msg, data=None):
        super(CourseEnrollmentError, self).__init__(msg)
        # Corresponding information to help resolve the error.
        self.data = data


class CourseModeNotFoundError(CourseEnrollmentError):
    """The requested course mode could not be found."""
    pass


class EnrollmentNotFoundError(CourseEnrollmentError):
    """The requested enrollment could not be found."""
    pass


class EnrollmentApiLoadError(CourseEnrollmentError):
    """The data API could not be loaded."""
    pass

DEFAULT_DATA_API = 'enrollment.data'


def get_enrollments(user_id):
    """Retrieves all the courses a user is enrolled in.

    Takes a user and retrieves all relative enrollments. Includes information regarding how the user is enrolled
    in the the course.

    Args:
        user_id (str): The username of the user we want to retrieve course enrollment information for.

    Returns:
        A list of enrollment information for the given user.

    Examples:
        >>> get_enrollments("Bob")
        [
            {
                "created": "2014-10-20T20:18:00Z",
                "mode": "honor",
                "is_active": True,
                "user": "Bob",
                "course": {
                    "course_id": "edX/DemoX/2014T2",
                    "enrollment_end": 2014-12-20T20:18:00Z,
                    "course_modes": [
                        {
                            "slug": "honor",
                            "name": "Honor Code Certificate",
                            "min_price": 0,
                            "suggested_prices": "",
                            "currency": "usd",
                            "expiration_datetime": null,
                            "description": null
                        }
                    ],
                    "enrollment_start": 2014-10-15T20:18:00Z,
                    "invite_only": False
                }
            },
            {
                "created": "2014-10-25T20:18:00Z",
                "mode": "verified",
                "is_active": True,
                "user": "Bob",
                "course": {
                    "course_id": "edX/edX-Insider/2014T2",
                    "enrollment_end": 2014-12-20T20:18:00Z,
                    "course_modes": [
                        {
                            "slug": "honor",
                            "name": "Honor Code Certificate",
                            "min_price": 0,
                            "suggested_prices": "",
                            "currency": "usd",
                            "expiration_datetime": null,
                            "description": null
                        }
                    ],
                    "enrollment_start": 2014-10-15T20:18:00Z,
                    "invite_only": True
                }
            }
        ]

    """
    return _data_api().get_course_enrollments(user_id)


def get_enrollment(user_id, course_id):
    """Retrieves all enrollment information for the user in respect to a specific course.

    Gets all the course enrollment information specific to a user in a course.

    Args:
        user_id (str): The user to get course enrollment information for.
        course_id (str): The course to get enrollment information for.

    Returns:
        A serializable dictionary of the course enrollment.

    Example:
        >>> get_enrollment("Bob", "edX/DemoX/2014T2")
        {
            "created": "2014-10-20T20:18:00Z",
            "mode": "honor",
            "is_active": True,
            "user": "Bob",
            "course": {
                "course_id": "edX/DemoX/2014T2",
                "enrollment_end": 2014-12-20T20:18:00Z,
                "course_modes": [
                    {
                        "slug": "honor",
                        "name": "Honor Code Certificate",
                        "min_price": 0,
                        "suggested_prices": "",
                        "currency": "usd",
                        "expiration_datetime": null,
                        "description": null
                    }
                ],
                "enrollment_start": 2014-10-15T20:18:00Z,
                "invite_only": False
            }
        }

    """
    return _data_api().get_course_enrollment(user_id, course_id)


def add_enrollment(user_id, course_id, mode='honor', is_active=True):
    """Enrolls a user in a course.

    Enrolls a user in a course. If the mode is not specified, this will default to 'honor'.

    Args:
        user_id (str): The user to enroll.
        course_id (str): The course to enroll the user in.
        mode (str): Optional argument for the type of enrollment to create. Ex. 'audit', 'honor', 'verified',
            'professional'. If not specified, this defaults to 'honor'.
        is_active (boolean): Optional argument for making the new enrollment inactive. If not specified, is_active
            defaults to True.

    Returns:
        A serializable dictionary of the new course enrollment.

    Example:
        >>> add_enrollment("Bob", "edX/DemoX/2014T2", mode="audit")
        {
            "created": "2014-10-20T20:18:00Z",
            "mode": "honor",
            "is_active": True,
            "user": "Bob",
            "course": {
                "course_id": "edX/DemoX/2014T2",
                "enrollment_end": 2014-12-20T20:18:00Z,
                "course_modes": [
                    {
                        "slug": "honor",
                        "name": "Honor Code Certificate",
                        "min_price": 0,
                        "suggested_prices": "",
                        "currency": "usd",
                        "expiration_datetime": null,
                        "description": null
                    }
                ],
                "enrollment_start": 2014-10-15T20:18:00Z,
                "invite_only": False
            }
        }
    """
    _validate_course_mode(course_id, mode)
    return _data_api().create_course_enrollment(user_id, course_id, mode, is_active)


def update_enrollment(user_id, course_id, mode=None, is_active=None):
    """Updates the course mode for the enrolled user.

    Update a course enrollment for the given user and course.

    Args:
        user_id (str): The user associated with the updated enrollment.
        course_id (str): The course associated with the updated enrollment.
        mode (str): The new course mode for this enrollment.

    Returns:
        A serializable dictionary representing the updated enrollment.

    Example:
        >>> update_enrollment("Bob", "edX/DemoX/2014T2", "honor")
        {
            "created": "2014-10-20T20:18:00Z",
            "mode": "honor",
            "is_active": True,
            "user": "Bob",
            "course": {
                "course_id": "edX/DemoX/2014T2",
                "enrollment_end": 2014-12-20T20:18:00Z,
                "course_modes": [
                    {
                        "slug": "honor",
                        "name": "Honor Code Certificate",
                        "min_price": 0,
                        "suggested_prices": "",
                        "currency": "usd",
                        "expiration_datetime": null,
                        "description": null
                    }
                ],
                "enrollment_start": 2014-10-15T20:18:00Z,
                "invite_only": False
            }
        }

    """
    _validate_course_mode(course_id, mode)
    enrollment = _data_api().update_course_enrollment(user_id, course_id, mode=mode, is_active=is_active)
    if enrollment is None:
        raise EnrollmentNotFoundError(
            u"Course Enrollment not found for user {user} in course {course}".format(user=user_id, course=course_id)
        )
    return enrollment


def get_course_enrollment_details(course_id):
    """Get the course modes for course. Also get enrollment start and end date, invite only, etc.

    Given a course_id, return a serializable dictionary of properties describing course enrollment information.

    Args:
        course_id (str): The Course to get enrollment information for.

    Returns:
        A serializable dictionary of course enrollment information.

    Example:
        >>> get_course_enrollment_details("edX/DemoX/2014T2")
        {
            "course_id": "edX/DemoX/2014T2",
            "enrollment_end": 2014-12-20T20:18:00Z,
            "course_modes": [
                {
                    "slug": "honor",
                    "name": "Honor Code Certificate",
                    "min_price": 0,
                    "suggested_prices": "",
                    "currency": "usd",
                    "expiration_datetime": null,
                    "description": null
                }
            ],
            "enrollment_start": 2014-10-15T20:18:00Z,
            "invite_only": False
        }

    """
    return _data_api().get_course_enrollment_info(course_id)


def _validate_course_mode(course_id, mode):
    """Checks to see if the specified course mode is valid for the course.

    If the requested course mode is not available for the course, raise an error with corresponding
    course enrollment information.

    'honor' is special cased. If there are no course modes configured, and the specified mode is
    'honor', return true, allowing the enrollment to be 'honor' even if the mode is not explicitly
    set for the course.

    Args:
        course_id (str): The course to check against for available course modes.
        mode (str): The slug for the course mode specified in the enrollment.

    Returns:
        None

    Raises:
        CourseModeNotFound: raised if the course mode is not found.
    """
    course_enrollment_info = _data_api().get_course_enrollment_info(course_id)
    course_modes = course_enrollment_info["course_modes"]
    available_modes = [m['slug'] for m in course_modes]
    if mode not in available_modes:
        msg = (
            u"Specified course mode '{mode}' unavailable for course {course_id}.  "
            u"Available modes were: {available}"
        ).format(
            mode=mode,
            course_id=course_id,
            available=", ".join(available_modes)
        )
        log.warn(msg)
        raise CourseModeNotFoundError(msg, course_enrollment_info)


def _data_api():
    """Returns a Data API.
    This relies on Django settings to find the appropriate data API.

    """
    # We retrieve the settings in-line here (rather than using the
    # top-level constant), so that @override_settings will work
    # in the test suite.
    api_path = getattr(settings, "ENROLLMENT_DATA_API", DEFAULT_DATA_API)

    try:
        return importlib.import_module(api_path)
    except (ImportError, ValueError):
        log.exception(u"Could not load module at '{path}'".format(path=api_path))
        raise EnrollmentApiLoadError(api_path)
