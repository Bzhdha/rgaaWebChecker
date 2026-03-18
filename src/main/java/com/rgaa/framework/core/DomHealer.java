package com.rgaa.framework.core;

import com.microsoft.playwright.Page;
import com.microsoft.playwright.Locator;
import java.util.Map;

/**
 * Moteur d'auto-guérison (Self-Healing).
 * Contient la logique d'injection du script JS de fuzzy matching.
 */
public class DomHealer {

    public Locator findBestMatch(Page page, ElementDescriptor target) {
        // Préparation des données pour le JS
        Map<String, Object> targetData = Map.of(
            "tagName", target.getTagName() != null ? target.getTagName() : "",
            "id", target.getId() != null ? target.getId() : "",
            "text", target.getText() != null ? target.getText() : "",
            "className", target.getClassName() != null ? target.getClassName() : "",
            "attributes", target.getAttributes()
        );

        // Exécution du script de fuzzy logic
        String resultSelector = (String) page.evaluate(getHealingScript(), targetData);

        if (resultSelector == null || resultSelector.isEmpty()) {
            return null;
        }

        System.out.println("🩹 [Auto-Healing] Élément retrouvé ! Nouveau sélecteur : " + resultSelector);
        return page.locator(resultSelector);
    }

    private String getHealingScript() {
        // Script JS identique à la version précédente (minifié pour la clarté)
        return "target => {" +
               "  const WEIGHTS = { TAG: 0.2, ID: 0.3, CLASS: 0.1, TEXT: 0.3, ATTR: 0.1 };" +
               "  const THRESHOLD = 0.6;" +
               "  function similarity(s1, s2) {" +
               "    if (!s1 || !s2) return 0.0;" +
               "    s1 = s1.toLowerCase(); s2 = s2.toLowerCase();" +
               "    if (s1 === s2) return 1.0;" +
               "    const len1 = s1.length, len2 = s2.length;" +
               "    const maxLen = Math.max(len1, len2);" +
               "    if (maxLen === 0) return 1.0;" +
               "    const d = [];" +
               "    for(let i=0; i<=len1; i++) d[i] = [i];" +
               "    for(let j=0; j<=len2; j++) d[0][j] = j;" +
               "    for(let i=1; i<=len1; i++) {" +
               "      for(let j=1; j<=len2; j++) {" +
               "        const cost = s1[i-1] === s2[j-1] ? 0 : 1;" +
               "        d[i][j] = Math.min(d[i-1][j]+1, d[i][j-1]+1, d[i-1][j-1]+cost);" +
               "      }" +
               "    }" +
               "    return 1.0 - (d[len1][len2] / maxLen);" +
               "  }" +
               "  function generateSelector(el) {" +
               "    if (el.id) return '#' + el.id;" +
               "    let path = [], parent;" +
               "    while (parent = el.parentNode) {" +
               "      path.unshift(`${el.tagName}:nth-child(${[].indexOf.call(parent.children, el)+1})`);" +
               "      el = parent;" +
               "      if (el.tagName === 'HTML') break;" +
               "    }" +
               "    return path.join(' > ');" +
               "  }" +
               "  const allElements = document.body.querySelectorAll('*');" +
               "  let bestMatch = null, maxScore = 0;" +
               "  for (const el of allElements) {" +
               "    if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE' || el.getBoundingClientRect().width === 0) continue;" +
               "    let currentScore = 0, totalWeight = 0;" +
               "    if (target.tagName) { totalWeight += WEIGHTS.TAG; if (el.tagName.toLowerCase() === target.tagName.toLowerCase()) currentScore += WEIGHTS.TAG; else if ((target.tagName === 'a' && el.tagName === 'button') || (target.tagName === 'button' && el.tagName === 'a')) currentScore += (WEIGHTS.TAG * 0.5); }" +
               "    if (target.id) { totalWeight += WEIGHTS.ID; currentScore += similarity(target.id, el.id) * WEIGHTS.ID; }" +
               "    if (target.text) { totalWeight += WEIGHTS.TEXT; const elText = el.innerText || el.textContent || ''; if (elText.length < 200) currentScore += similarity(target.text, elText.trim()) * WEIGHTS.TEXT; }" +
               "    if (target.className) { totalWeight += WEIGHTS.CLASS; currentScore += similarity(target.className, el.className) * WEIGHTS.CLASS; }" +
               "    const finalScore = totalWeight > 0 ? currentScore / totalWeight : 0;" +
               "    if (finalScore > maxScore) { maxScore = finalScore; bestMatch = el; }" +
               "  }" +
               "  return (bestMatch && maxScore >= THRESHOLD) ? generateSelector(bestMatch) : null;" +
               "}";
    }
}
