/* ============================================================
   BLINK COMMUNICATION - SMART SUGGESTIONS ENGINE
   الملف ده هو "مخ الاقتراحات" المستقل:
   1. إعدادات سهلة فوق (CONFIG)
   2. توحيد الحروف العربية (أ إ آ -> ا)
   3. شجرة بحث سريعة (Trie) للـ 22,000 كلمة
   4. ذاكرة شخصية بتتعلّم من المريض (localStorage)
   5. توقّع الكلمة الجاية + إكمال الكلمة الحالية
   6. فيشة جاهزة للـ LLM في المستقبل + رسم الأزرار
============================================================ */

(function (global) {
  "use strict";

  /* ==========================================================
     1) الإعدادات (CONFIG)
     هنا بتغيّر أي إعداد أساسي من غير ما تدخل في تفاصيل الكود
  ========================================================== */
  const CONFIG = {
    maxSuggestions: 4, // أقصى عدد زراير اقتراحات تظهر على الشاشة
    useLLM: false, // خليها true لما الباك إند يجهز رابط الـ LLM
    llmEndpoint: "", // رابط الـ API اللي هيديهولك بتاع الباك إند
    llmTimeoutMs: 1200, // أقصى وقت نستناه من السيرفر (1.2 ثانية) قبل ما نكمل محلي
    debounceMs: 250, // نستنى 250 مللي ثانية قبل ما نبعت للسيرفر عشان منبعتش طلبات كتير
    storageKey: "blink_suggestions_memory_v1" // اسم المكان المحفوظ في localStorage
  };

  /* ==========================================================
     2) توحيد الحروف (Normalization)
     عشان لما المريض يكتب "ا" يفهم إن قصده (أ / إ / آ / ا)
  ========================================================== */
  function normalizeText(text, lang) {
    if (!text) return "";

    if (lang === "en") {
      return text.toLowerCase().trim();
    }

    return text
      .replace(/[\u064B-\u065F\u0670\u0640]/g, "") // يشيل التشكيل والتطويل
      .replace(/[أإآ]/g, "ا") // يوحد كل أشكال الألف
      .replace(/ى/g, "ي") // يوحد الألف اللينة والياء
      .replace(/ة/g, "ه") // يقرب التاء المربوطة والهاء في البحث
      .trim();
  }

  /* ==========================================================
     3) شجرة البحث السريعة (Trie)
     بدل ما يدور في 22,000 كلمة واحدة واحدة، بيدخل حرف بحرف
     وبيخزن أشهر 25 كلمة عند كل خطوة عشان الرد يبقى في أقل من 1ms
  ========================================================== */
  function createTrieNode() {
    return {
      children: Object.create(null),
      topIndices: [] // أرقام أشهر كلمات بتبدأ بالحروف دي
    };
  }

  function buildTrieForLanguage(words, lang) {
    const root = createTrieNode();

    for (let index = 0; index < words.length; index++) {
      const word = words[index];
      const norm = normalizeText(word, lang);
      if (!norm) continue;

      let node = root;
      for (let i = 0; i < norm.length; i++) {
        const ch = norm[i];
        if (!node.children[ch]) {
          node.children[ch] = createTrieNode();
        }
        node = node.children[ch];

        // نخزن بس أول 25 كلمة لأن المصفوفة أصلًا مترتبة من الأشهر للأقل
        if (node.topIndices.length < 25) {
          node.topIndices.push(index);
        }
      }
    }

    return root;
  }

  // تجهيز الشجرتين (عربي وإنجليزي) مرة واحدة أول ما الصفحة تفتح
  const dict = global.BLINK_DICTIONARY || {
    starters: { ar: [], en: [] },
    nextWords: { ar: {}, en: {} },
    words: { ar: [], en: [] }
  };

  const tries = {
    ar: buildTrieForLanguage(dict.words.ar || [], "ar"),
    en: buildTrieForLanguage(dict.words.en || [], "en")
  };

  // بناء خريطة موحدة لجدول الكلمات المتتالية عشان البحث السريع
  const normalizedNextWords = { ar: Object.create(null), en: Object.create(null) };
  ["ar", "en"].forEach((lang) => {
    const table = (dict.nextWords && dict.nextWords[lang]) || {};
    Object.keys(table).forEach((key) => {
      const normKey = key
        .split(/\s+/)
        .map((w) => normalizeText(w, lang))
        .join(" ");
      normalizedNextWords[lang][normKey] = table[key];
    });
  });

  function searchTriePrefix(prefixNorm, lang) {
    const root = tries[lang];
    const wordList = (dict.words && dict.words[lang]) || [];
    if (!root || !prefixNorm) return [];

    let node = root;
    for (let i = 0; i < prefixNorm.length; i++) {
      const ch = prefixNorm[i];
      if (!node.children[ch]) {
        return []; // مفيش ولا كلمة بتبدأ بالحروف دي
      }
      node = node.children[ch];
    }

    return node.topIndices.map((idx) => wordList[idx]);
  }

  /* ==========================================================
     4) الذاكرة الشخصية للمريض (localStorage)
     بتحفظ الكلمات والجمل اللي المريض بيختارها كتير
  ========================================================== */
  function getEmptyMemory() {
    return {
      wordCounts: { ar: {}, en: {} },
      pairCounts: { ar: {}, en: {} }
    };
  }

  function loadMemory() {
    try {
      const raw = global.localStorage.getItem(CONFIG.storageKey);
      if (!raw) return getEmptyMemory();
      const parsed = JSON.parse(raw);
      return {
        wordCounts: parsed.wordCounts || { ar: {}, en: {} },
        pairCounts: parsed.pairCounts || { ar: {}, en: {} }
      };
    } catch (err) {
      return getEmptyMemory();
    }
  }

  let personalMemory = loadMemory();

  function saveMemory() {
    try {
      global.localStorage.setItem(CONFIG.storageKey, JSON.stringify(personalMemory));
    } catch (err) {
      // نتجاهل بهدوء لو المتصفح مانع التخزين
    }
  }

  // تسجيل كلمة اختارها المريض وربطها بالكلمة اللي قبلها
  function recordWordUse(word, prevWord, lang) {
    const cleanWord = (word || "").trim();
    if (!cleanWord) return;

    if (!personalMemory.wordCounts[lang]) personalMemory.wordCounts[lang] = {};
    if (!personalMemory.pairCounts[lang]) personalMemory.pairCounts[lang] = {};

    // نزود رصيد الكلمة نفسها
    personalMemory.wordCounts[lang][cleanWord] =
      (personalMemory.wordCounts[lang][cleanWord] || 0) + 1;

    // لو فيه كلمة قبلها، نزود رصيد إنها بتيجي بعدها
    if (prevWord) {
      const prevNorm = normalizeText(prevWord, lang);
      if (prevNorm) {
        if (!personalMemory.pairCounts[lang][prevNorm]) {
          personalMemory.pairCounts[lang][prevNorm] = {};
        }
        personalMemory.pairCounts[lang][prevNorm][cleanWord] =
          (personalMemory.pairCounts[lang][prevNorm][cleanWord] || 0) + 1;
      }
    }

    saveMemory();
  }

  // تتعلم من جملة كاملة (مفيدة جدًا لما المريض يدوس زر النطق)
  function learnSentence(fullText, lang) {
    const tokens = (fullText || "").trim().split(/\s+/).filter(Boolean);
    for (let i = 0; i < tokens.length; i++) {
      const current = tokens[i];
      const prev = i > 0 ? tokens[i - 1] : null;
      recordWordUse(current, prev, lang);
    }
  }

  function clearMemory() {
    personalMemory = getEmptyMemory();
    saveMemory();
  }

  // تجيب الكلمات اللي المريض استخدمها قبل كده بعد كلمة معينة
  function getPersonalNextWords(prevWordNorm, lang) {
    const pairs = (personalMemory.pairCounts[lang] || {})[prevWordNorm];
    if (!pairs) return [];
    return Object.keys(pairs).sort((a, b) => pairs[b] - pairs[a]);
  }

  // تجيب كلمات المريض الشخصية اللي بتبدأ بحروف معينة
  function getPersonalMatchingWords(prefixNorm, lang) {
    const counts = personalMemory.wordCounts[lang] || {};
    return Object.keys(counts)
      .filter((w) => normalizeText(w, lang).startsWith(prefixNorm))
      .sort((a, b) => counts[b] - counts[a]);
  }

  /* ==========================================================
     5) تحليل النص ومخ التوقّع (Core Engine)
     بيفهم إحنا في أول الجملة ولا بعد مسافة ولا في نص كلمة
  ========================================================== */
  function parseInput(rawText) {
    const text = rawText || "";
    const trimmedStart = text.trimStart();

    if (!trimmedStart) {
      return {
        mode: "empty",
        currentFragment: "",
        completedWords: [],
        lastWord: "",
        lastTwoWords: ""
      };
    }

    const endsWithSpace = /\s$/.test(text);
    const tokens = trimmedStart.trim().split(/\s+/).filter(Boolean);

    if (endsWithSpace) {
      const lastWord = tokens[tokens.length - 1] || "";
      const lastTwoWords =
        tokens.length >= 2 ? tokens.slice(-2).join(" ") : "";
      return {
        mode: "next-word",
        currentFragment: "",
        completedWords: tokens,
        lastWord: lastWord,
        lastTwoWords: lastTwoWords
      };
    }

    const currentFragment = tokens[tokens.length - 1] || "";
    const before = tokens.slice(0, -1);
    const lastWord = before[before.length - 1] || "";
    const lastTwoWords =
      before.length >= 2 ? before.slice(-2).join(" ") : "";

    return {
      mode: "complete-word",
      currentFragment: currentFragment,
      completedWords: before,
      lastWord: lastWord,
      lastTwoWords: lastTwoWords
    };
  }

  // دالة مساعدة تمنع تكرار نفس الكلمة في الاقتراحات
  function collectUnique(targetList, candidates, lang, excludeNormSet, limit) {
    for (let i = 0; i < candidates.length; i++) {
      if (targetList.length >= limit) break;
      const word = candidates[i];
      const norm = normalizeText(word, lang);
      if (!norm || excludeNormSet.has(norm)) continue;
      excludeNormSet.add(norm);
      targetList.push(word);
    }
  }

  function getContextPredictionsForTokens(tokens, lang, excludeNormSet) {
    const results = [];
    const seen = excludeNormSet || new Set();
    const limit = CONFIG.maxSuggestions;

    const lastWord = tokens[tokens.length - 1] || "";
    const lastTwoWords = tokens.length >= 2 ? tokens.slice(-2).join(" ") : "";

    if (lastWord) {
      seen.add(normalizeText(lastWord, lang));
    }

    const prevNorm = normalizeText(lastWord, lang);
    const twoNorm = lastTwoWords
      ? lastTwoWords
          .split(/\s+/)
          .map((w) => normalizeText(w, lang))
          .join(" ")
      : "";

    // 1. أولًا: اللي المريض نفسه متعود يختاره بعد الكلمة دي
    if (prevNorm) {
      collectUnique(results, getPersonalNextWords(prevNorm, lang), lang, seen, limit);
    }

    // 2. ثانيًا: سياق آخر كلمتين من القاموس (زي "انا عايز")
    if (twoNorm && normalizedNextWords[lang][twoNorm]) {
      collectUnique(
        results,
        normalizedNextWords[lang][twoNorm],
        lang,
        seen,
        limit
      );
    }

    // 3. ثالثًا: سياق آخر كلمة من القاموس (زي "عايز")
    if (prevNorm && normalizedNextWords[lang][prevNorm]) {
      collectUnique(
        results,
        normalizedNextWords[lang][prevNorm],
        lang,
        seen,
        limit
      );
    }

    return results;
  }

  function getContextPredictions(parsed, lang) {
    return getContextPredictionsForTokens(parsed.completedWords, lang);
  }

  // ترجع تفاصيل الاقتراحات: الكلمة وهل هي تكملة للكلمة الحالية ولا كلمة جديدة بعدها
  function getSuggestionItemsSync(rawText, lang) {
    const activeLang = lang === "en" ? "en" : "ar";
    const parsed = parseInput(rawText);
    const limit = CONFIG.maxSuggestions;
    const items = [];
    const seen = new Set();

    function pushWords(wordsList, actionType) {
      for (let i = 0; i < wordsList.length; i++) {
        if (items.length >= limit) break;
        const word = wordsList[i];
        const norm = normalizeText(word, activeLang);
        if (!norm || seen.has(norm)) continue;
        seen.add(norm);
        items.push({ word: word, action: actionType });
      }
    }

    // الحالة أ: المربع فاضي تمامًا
    if (parsed.mode === "empty") {
      const topPersonal = Object.keys(personalMemory.wordCounts[activeLang] || {})
        .sort(
          (a, b) =>
            personalMemory.wordCounts[activeLang][b] -
            personalMemory.wordCounts[activeLang][a]
        )
        .slice(0, 2);

      pushWords(topPersonal, "next");
      pushWords((dict.starters && dict.starters[activeLang]) || [], "next");
      return items;
    }

    // الحالة ب: المريض لسه مخلص كلمة ودايس مسافة
    if (parsed.mode === "next-word") {
      const contextMatches = getContextPredictionsForTokens(
        parsed.completedWords,
        activeLang
      );
      pushWords(contextMatches, "next");

      if (items.length < limit) {
        if (parsed.lastWord) seen.add(normalizeText(parsed.lastWord, activeLang));
        pushWords((dict.starters && dict.starters[activeLang]) || [], "next");
        pushWords(
          ((dict.words && dict.words[activeLang]) || []).slice(0, 20),
          "next"
        );
      }
      return items;
    }

    // الحالة ج: المريض لسه مداسش مسافة
    const prefixNorm = normalizeText(parsed.currentFragment, activeLang);
    const allTokensNow = parsed.completedWords.concat([parsed.currentFragment]);

    // ج-1: لو الكلمة اللي كتبها كاملة وموجودة في سياق الكلمة الجاية (زي "عايز" أو "انا عايز" من غير مسافة)
    const directNextWords = getContextPredictionsForTokens(allTokensNow, activeLang);
    if (directNextWords.length > 0) {
      // نعرض التوقعات اللي بتيجي بعد الكلمة فورًا، ولو الكلمة قصيرة (حرفين أو أقل) نسيب مكان لتكملة محتملة
      const maxNext = prefixNorm.length <= 2 ? limit - 1 : limit;
      for (let i = 0; i < directNextWords.length && items.length < maxNext; i++) {
        const w = directNextWords[i];
        const norm = normalizeText(w, activeLang);
        if (!norm || seen.has(norm)) continue;
        seen.add(norm);
        items.push({ word: w, action: "next" });
      }

      if (items.length < limit) {
        const longerMatches = searchTriePrefix(prefixNorm, activeLang).filter(
          (w) => normalizeText(w, activeLang) !== prefixNorm
        );
        pushWords(longerMatches, "complete");
      }

      return items;
    }

    // ج-2: لسه في نص كلمة ومكتملتش، نكملها عادي من السياق + الذاكرة + الـ Trie
    const contextWords = getContextPredictions(parsed, activeLang).filter((w) =>
      normalizeText(w, activeLang).startsWith(prefixNorm)
    );
    pushWords(contextWords, "complete");

    const personalMatches = getPersonalMatchingWords(prefixNorm, activeLang);
    pushWords(personalMatches, "complete");

    const trieMatches = searchTriePrefix(prefixNorm, activeLang);
    pushWords(trieMatches, "complete");

    return items;
  }

  function getSuggestionsSync(rawText, lang) {
    return getSuggestionItemsSync(rawText, lang).map((item) => item.word);
  }

  /* ==========================================================
     6) فيشة الـ LLM الجاهزة (للمستقبل) + تطبيق الاقتراح + رسم الأزرار
  ========================================================== */
  let currentText = "";
  let currentLang = "ar";
  let containerElements = [];
  let onSelectCallback = null;

  let llmDebounceTimer = null;
  let llmAbortController = null;
  const llmCache = Object.create(null);

  // دالة دمج الكلمة المختارة مع النص الحالي
  function buildTextAfterSuggestion(rawText, chosenWord, actionType) {
    const parsed = parseInput(rawText);

    if (parsed.mode === "empty") {
      return chosenWord + " ";
    }

    if (parsed.mode === "next-word") {
      return rawText.trimEnd() + " " + chosenWord + " ";
    }

    // لو المستخدم اختار الكلمة الجاية وهو لسه مداسش مسافة (مثلاً كتب "عايز" وداس "اشرب")
    const isNextWord =
      actionType === "next" ||
      (actionType !== "complete" &&
        !normalizeText(chosenWord, currentLang).startsWith(
          normalizeText(parsed.currentFragment, currentLang)
        ));

    if (isNextWord) {
      return rawText.trimEnd() + " " + chosenWord + " ";
    }

    // لو في نص كلمة: نشيل الجزء الناقص ونحط الكلمة الكاملة + مسافة
    const beforeText = parsed.completedWords.join(" ");
    return (beforeText ? beforeText + " " : "") + chosenWord + " ";
  }

  function resolveContainers(containersInput) {
    if (!containersInput) return [];
    const list = Array.isArray(containersInput)
      ? containersInput
      : [containersInput];

    return list
      .map((item) =>
        typeof item === "string" ? global.document.querySelector(item) : item
      )
      .filter(Boolean);
  }

  function renderSuggestions(suggestions, lang) {
    if (!containerElements.length) return;
    const direction = lang === "en" ? "ltr" : "rtl";

    containerElements.forEach((container) => {
      container.innerHTML = "";
      container.style.direction = direction;

      if (!suggestions.length) {
        container.classList.add("is-empty");
        return;
      }

      container.classList.remove("is-empty");

      suggestions.forEach((entry) => {
        const word = typeof entry === "string" ? entry : entry.word;
        const actionType = typeof entry === "string" ? "auto" : entry.action;

        const btn = global.document.createElement("button");
        btn.type = "button";
        btn.className = "blink-suggestion-btn";
        btn.textContent = word;
        btn.setAttribute("data-suggestion", word);
        btn.setAttribute("data-action", actionType);

        btn.addEventListener("click", () => {
          const parsed = parseInput(currentText);
          const prevForLearning =
            parsed.mode === "complete-word" && actionType === "next"
              ? parsed.currentFragment
              : parsed.lastWord;

          recordWordUse(word, prevForLearning, currentLang);

          const updatedText = buildTextAfterSuggestion(
            currentText,
            word,
            actionType
          );
          if (typeof onSelectCallback === "function") {
            onSelectCallback(updatedText, word);
          } else {
            update(updatedText, currentLang);
          }
        });

        container.appendChild(btn);
      });
    });
  }

  // طلب اقتراحات أذكى من سيرفر الـ LLM (يشتغل فقط لو useLLM = true)
  function requestLLMSuggestions(text, lang) {
    if (!CONFIG.useLLM || !CONFIG.llmEndpoint) return;

    const cacheKey = lang + "::" + text;
    if (llmCache[cacheKey]) {
      renderSuggestions(llmCache[cacheKey], lang);
      return;
    }

    if (llmDebounceTimer) clearTimeout(llmDebounceTimer);
    if (llmAbortController) llmAbortController.abort();

    llmDebounceTimer = setTimeout(async () => {
      llmAbortController = new AbortController();
      const timeoutId = setTimeout(
        () => llmAbortController.abort(),
        CONFIG.llmTimeoutMs
      );

      try {
        const res = await fetch(CONFIG.llmEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: text,
            lang: lang,
            limit: CONFIG.maxSuggestions
          }),
          signal: llmAbortController.signal
        });

        clearTimeout(timeoutId);
        if (!res.ok) return;

        const data = await res.json();
        if (
          data &&
          Array.isArray(data.suggestions) &&
          data.suggestions.length > 0 &&
          currentText === text &&
          currentLang === lang
        ) {
          const clean = data.suggestions.slice(0, CONFIG.maxSuggestions);
          llmCache[cacheKey] = clean;
          renderSuggestions(clean, lang);
        }
      } catch (err) {
        // لو السيرفر اتأخر أو وقع، الاقتراحات المحلية شغالة أوريدي
      }
    }, CONFIG.debounceMs);
  }

  function update(text, lang) {
    currentText = text || "";
    currentLang = lang === "en" ? "en" : "ar";

    // 1. نعرض الاقتراحات المحلية فورًا (أقل من 2ms)
    const localItems = getSuggestionItemsSync(currentText, currentLang);
    renderSuggestions(localItems, currentLang);

    // 2. لو الـ LLM متفعّل، نسأله في الخلفية عند المسافات أو الجمل
    if (CONFIG.useLLM && currentText.trim().length > 0) {
      requestLLMSuggestions(currentText, currentLang);
    }

    return localItems.map((item) => item.word);
  }

  function init(options) {
    const opts = options || {};
    if (opts.config) {
      Object.assign(CONFIG, opts.config);
    }
    containerElements = resolveContainers(opts.containers);
    onSelectCallback = typeof opts.onSelect === "function" ? opts.onSelect : null;

    update(opts.initialText || "", opts.lang || "ar");
  }

  // تصدير الواجهة البسيطة اللي أي حد يقدر يستخدمها
  global.BlinkSuggestions = {
    config: CONFIG,
    init: init,
    update: update,
    getSuggestionsSync: getSuggestionsSync,
    buildTextAfterSuggestion: buildTextAfterSuggestion,
    learnSentence: learnSentence,
    clearMemory: clearMemory
  };
})(window);
