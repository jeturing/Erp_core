/** @odoo-module **/
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : https://store.webkul.com/license.html/ */

import publicWidget from "@web/legacy/js/public/public_widget";
publicWidget.registry.odoo_rest = publicWidget.Widget.extend({
  selector: "#testRest",

  events: {
    "click #dark_mode": "_darkModeOn",
    "click #light_mode": "_lightModeOn",
    'click .sidebarCollapse': '_onsidebarCollapse',

    "click #restfile": "downloadFile",
    "click #home_a": "_get_home",
    "click #searchlink": "_get_searchrequest",
    "click #viewrecord_a": "_get_viewrecord",
    "click #updaterequest_a": "_get_updaterequest",
    "click #deleterecord_a": "_get_deleterecord",
    "click #modelschema_a": "_get_modelschema",
    "click #createrecord_a": "_get_createrecord",
    "click #executefunction_a": "_get_executefunction",
    "click #generatetoken_a": "_get_generatetoken",
    "click #jsondatafile_a": "_get_jsondatafile",
    "click #swaggerui_a": "_get_swaggerUi",
    "click .back_button": "_get_back_rest_tree_view",
  },

  init() {
    this._super(...arguments);
    this.rpc = this.bindService("rpc");
  },

  start: function () {
    var def = this._super.apply(this, arguments);

    const swaggerUI = SwaggerUIBundle({
      url: odoo.rest.serverBaseUrl + "/generate/swagger/rest/docs",
      dom_id: "#swagger-ui",
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
      plugins: [SwaggerUIBundle.plugins.DownloadUrl],
      layout: "BaseLayout",
      operationsSorter: (elem1, elem2) => {
        let methodsOrder = [
          "get",
          "post",
          "put",
          "delete",
          "patch",
          "options",
          "trace",
        ];
        let result =
          methodsOrder.indexOf(elem1.get("method")) -
          methodsOrder.indexOf(elem2.get("method"));
        return result === 0
          ? elem1.get("path").localeCompare(elem2.get("path"))
          : result;
      },
      tagsSorter: "alpha",
      requestInterceptor: (req) => {
        req.headers[odoo.rest.databaseHeader] = odoo.rest.databaseName;
        return req;
      },
    });

    swaggerUI.initOAuth({
      additionalQueryStringParams: {
        [odoo.rest.databaseParam]: odoo.rest.databaseName,
      },
    });

    return def;
  },

  _openNav: async function (ev) {
    var w = window.innerWidth;
    var h = window.innerHeight;

    document.getElementById("mySidebar").style.width = "250px";
    document.getElementById("mySidebar").style.paddingLeft = "15px";
    document.getElementById("mainrow").style.paddingLeft = "30px";
    document.getElementById("mySidebar").style.paddingRight = "15px";

    if (w > 768) {
      document.getElementById("main").style.width = "80%";
      document.getElementById("mySidebar").style.position = "fixed";
      document.getElementById("main").style.marginLeft = "250px";
    } else {
      document.getElementById("main").style.width = "100%";
      document.getElementById("main").style.marginLeft = "0px";
    }
  },

  closeNav: async function (ev) {
    $("#openbtn").show();
    document.getElementById("mainrow").style.paddingLeft = "50px";
    document.getElementById("mySidebar").style.width = "0";
    document.getElementById("main").style.width = "100%";
    document.getElementById("main").style.marginLeft = "0px";
    document.getElementById("mySidebar").style.paddingLeft = "0px";
    document.getElementById("mySidebar").style.paddingRight = "0px";
  },

  downloadFile: async function (ev) {
    this.rpc("/web/dataset/call_kw/rest.api/download_file", {
      model: "rest.api",
      method: "download_file",
      args: ["self"],
      kwargs :{}
    }).then(function (data) {
      if (data) {
        location.href = data;
      } else {
        alert("Authentication Failed...");
      }
    });
  },


  _get_home: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".home_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#home").show();
  },

  _get_searchrequest: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".searchlink").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#searchrequest").show();
  },

  _get_viewrecord: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".viewrecord_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#viewrecord").show();
  },

  _get_updaterequest: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".updaterequest_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#updaterequest").show();
  },

  _get_deleterecord: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".deleterecord_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#deleterecord").show();
  },

  _get_modelschema: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".modelschema_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#modelschema").show();
  },

  _get_createrecord: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".createrecord_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#createrecord").show();
  },

  _get_executefunction: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".executefunction_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#executefunction").show();
  },

  _get_generatetoken: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".generatetoken_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#generatetoken").show();
  },

  _get_jsondatafile: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".jsondatafile_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#jsondatafile").show();
  },

  _get_swaggerUi: async function (ev) {
    $(".sideMenuOptions").css("-webkit-text-fill-color", "white");
    $(".swaggerui_a").css("-webkit-text-fill-color", "red");
    $(".request").hide();
    $("#swagger-ui").show();
  },


  _onsidebarCollapse: function() {
    $('#sidebar').toggleClass('active');
    if($('#sidebar').hasClass("active")){
        $('#sidebar').css('position', 'fixed');
        $('#content').css('margin-left', '250px');
    }
    else{
        $('#sidebar').css('position', 'relative');
        $('#content').css('margin-left', '0');

    }
  },

 _darkModeOn: function () {
    $("#light_mode").show();
    $("#dark_mode").hide();
    $("#swagger-ui").addClass("dark_background");
    $(".rest_docs_standalone").addClass("dark_background");
  },
  
  _lightModeOn: function () {
    $("#dark_mode").show();
    $("#light_mode").hide();
    $("#swagger-ui").removeClass("dark_background");
    $(".rest_docs_standalone").removeClass("dark_background");
  },

  _get_back_rest_tree_view: function () {
    this.rpc("/web/dataset/call_kw/rest.api/riderct_rest_url", {
      model: "rest.api",
      method: "riderct_rest_url",
      args: ["self"],
      kwargs :{}
    }).then(function (data) {
      location.href = data;
    });
  },
});
