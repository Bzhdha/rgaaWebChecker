package com.rgaa.framework.pages;

import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.TimeoutError;
import com.rgaa.framework.core.DomHealer;
import com.rgaa.framework.core.ElementDescriptor;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Classe parente de tous les Page Objects.
 * Fournit les méthodes d'interaction "Smart" (avec auto-healing).
 */
public abstract class BasePage {
    protected final Page page;
    private final DomHealer healer;

    public BasePage(Page page) {
        this.page = page;
        this.healer = new DomHealer();
    }

    /**
     * Clic résilient. Tente le sélecteur, puis l'auto-healing.
     */
    protected void click(String selector, ElementDescriptor descriptor) {
        try {
            // Timeout réduit pour déclencher l'auto-healing rapidement si besoin
            page.locator(selector).click(new Locator.ClickOptions().setTimeout(2000));
        } catch (TimeoutError e) {
            System.out.println("⚠️ Clic échoué sur '" + selector + "'. Recherche auto-healing...");
            Locator healed = healer.findBestMatch(page, descriptor);
            if (healed != null) {
                healed.click();
            } else {
                throw new RuntimeException("❌ Élément introuvable malgré l'auto-healing : " + descriptor.getText());
            }
        }
    }

    /**
     * Remplissage résilient.
     */
    protected void fill(String selector, ElementDescriptor descriptor, String value) {
        try {
            page.locator(selector).fill(value, new Locator.FillOptions().setTimeout(2000));
        } catch (TimeoutError e) {
            System.out.println("⚠️ Remplissage échoué sur '" + selector + "'. Recherche auto-healing...");
            Locator healed = healer.findBestMatch(page, descriptor);
            if (healed != null) {
                healed.fill(value);
            } else {
                throw new RuntimeException("❌ Champ introuvable malgré l'auto-healing : " + descriptor.getText());
            }
        }
    }

    /**
     * Assertion de texte résiliente.
     */
    protected void assertTextContains(String selector, ElementDescriptor descriptor, String expectedText) {
        try {
            Locator loc = page.locator(selector);
            loc.waitFor(new Locator.WaitForOptions().setTimeout(2000));
            assertTrue(loc.textContent().contains(expectedText));
        } catch (TimeoutError e) {
            System.out.println("⚠️ Vérification échouée sur '" + selector + "'. Recherche auto-healing...");
            Locator healed = healer.findBestMatch(page, descriptor);
            if (healed != null) {
                String actualText = healed.textContent();
                assertTrue(actualText.contains(expectedText), 
                    "Texte attendu '" + expectedText + "' non trouvé. Texte réel : '" + actualText + "'");
            } else {
                throw new RuntimeException("❌ Élément de texte introuvable.");
            }
        }
    }
}
