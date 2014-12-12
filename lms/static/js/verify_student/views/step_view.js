/**
 * Base view for defining steps in the payment/verification flow.
 *
 * Each step view lazy-loads its underscore template.
 * This reduces the size of the initial page, since we don't
 * need to include the DOM structure for each step
 * in the initial load.
 *
 * Step subclasses are responsible for defining a template
 * and installing custom event handlers (including buttons
 * to move to the next step).
 *
 * The superclass is responsible for downloading the underscore
 * template and rendering it, using context received from
 * the server (in data attributes on the initial page load).
 *
 */
 var edx = edx || {};

 (function( $, _, _s, Backbone ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.StepView = Backbone.View.extend({

        initialize: function( obj ) {
            this.templateUrl = obj.templateUrl || "";
            this.stepData = obj.stepData || {};
            this.nextStepNum = obj.nextStepNum || "";
            this.nextStepTitle = obj.nextStepTitle || "";

            /* Mix non-conflicting functions from underscore.string
             * (all but include, contains, and reverse) into the
             * Underscore namespace
             */
            _.mixin( _s.exports() );
        },

        render: function() {
            // TODO: handle failure condition
            if ( !this.renderedHtml && this.templateUrl) {
                $.ajax({
                    url: this.templateUrl,
                    type: 'GET',
                    context: this,
                    success: this.handleResponse
                });
            }
            else {
                $( this.el ).html( this.renderedHtml );
                this.postRender();
            }
        },

        handleResponse: function( data ) {
            var context;

            context = {
                nextStepNum: this.nextStepNum,
                nextStepTitle: this.nextStepTitle
            };

            // Include step-specific information
            _.extend( context, this.stepData );

            this.renderedHtml = _.template( data, context );
            $( this.el ).html( this.renderedHtml );

            this.postRender();
        },

        postRender: function() {
            // Sub-classes can override this method
            // to install custom event handlers.
        },

        nextStep: function() {
            this.trigger('next-step');
        }

    });

 })( jQuery, _, _.str, Backbone );
