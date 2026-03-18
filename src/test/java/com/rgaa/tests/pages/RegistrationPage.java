package com.rgaa.tests.pages;

import com.microsoft.playwright.Page;
import com.rgaa.framework.pages.BasePage;
import com.rgaa.framework.core.ElementDescriptor;

public class RegistrationPage extends BasePage {

    // --- DÉFINITIONS (Sélecteurs + Descripteurs) ---
    
    // Champ Prénom
    private static final String INPUT_FIRSTNAME_SEL = "#firstname"; // Ancien ID
    private static final ElementDescriptor INPUT_FIRSTNAME_DESC = 
        new ElementDescriptor("input", "firstname", "")
            .withAttribute("type", "text")
            .withAttribute("placeholder", "Ex: Jean");

    // Bouton Valider
    private static final String BTN_SUBMIT_SEL = ".btn-create"; // Ancienne classe
    private static final ElementDescriptor BTN_SUBMIT_DESC = 
        new ElementDescriptor("button", "", "Créer mon compte");

    // Message Confirmation
    private static final String MSG_CONFIRM_SEL = "h1.welcome-msg"; // Ancien header
    private static final ElementDescriptor MSG_CONFIRM_DESC = 
        new ElementDescriptor("h1", "welcome-msg", "Bienvenue");


    public RegistrationPage(Page page) {
        super(page);
    }

    // --- ACTIONS MÉTIER ---

    public void enterFirstname(String firstname) {
        fill(INPUT_FIRSTNAME_SEL, INPUT_FIRSTNAME_DESC, firstname);
    }

    public void submitForm() {
        click(BTN_SUBMIT_SEL, BTN_SUBMIT_DESC);
    }

    public void checkConfirmationMessage(String expectedText) {
        assertTextContains(MSG_CONFIRM_SEL, MSG_CONFIRM_DESC, expectedText);
    }
}
