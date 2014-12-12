/**
 * Entry point for the payment/verification flow.
 * This loads the base view, which in turn loads
 * subviews for each step in the flow.
 *
 * We pass some information to the base view
 * using "data-" attributes on the parent div.
 * See "pay_and_verify.html" for the exact attribute names.
 *
 */
var edx = edx || {};

(function($) {
    'use strict';
    var el = $('#pay-and-verify-container');

    edx.verify_student = edx.verify_student || {};

    // Initialize the base view, passing in information
    // from the data attributes on the parent div.
    //
    // The data attributes capture information that only
    // the server knows about, such as the course and course mode info,
    // full URL paths to static underscore templates,
    // and some messaging.
    //
    return new edx.verify_student.PayAndVerifyView({
        displaySteps: el.data('display-steps'),
        currentStep: el.data('current-step'),
        stepInfo: {
            'intro-step': {
                introTitle: el.data('intro-title'),
                introMsg: el.data('intro-msg'),
                requirements: el.data('requirements')
            },
            'make-payment-step': {
                courseKey: el.data('course-key'),
                minPrice: el.data('course-mode-min-price'),
                suggestedPrices: (el.data('course-mode-suggested-prices') || "").split(","),
                currency: el.data('course-mode-currency'),
                purchaseEndpoint: el.data('purchase-endpoint')
            },
            'payment-confirmation-step': {
                courseName: el.data('course-name'),
                courseStartDate: el.data('course-start-date'),
                coursewareUrl: el.data('courseware-url')
            },
            'review-photos-step': {
                fullName: el.data('full-name')
            }
        }
    }).render();
})(jQuery);
