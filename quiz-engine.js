/* ================================================================
   quiz-engine.js  —  Quiz bootstrapper.
   Leaves shared behavior to exam-engine-shared.js.
   ================================================================ */
(function () {
  'use strict';

  var _cs = document.currentScript;
  var ENGINE_BASE = _cs ? _cs.src.replace(/[^\/]*$/, '') : (window.__QUIZ_ENGINE_BASE || '');

  window.__MU61_EXAM_BOOT = {
    kind: 'quiz',
    engineBase: ENGINE_BASE
  };

  document.write('<scr' + 'ipt src="' + ENGINE_BASE + 'exam-engine-shared.js"><\/scr' + 'ipt>');
})();
