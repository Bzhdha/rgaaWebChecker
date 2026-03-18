package com.rgaa.tests.steps;

import com.microsoft.playwright.*;
import com.rgaa.tests.pages.RegistrationPage;
import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.en.*;

public class RegistrationSteps {
    private Playwright playwright;
    private Browser browser;
    private Page page;
    private RegistrationPage registrationPage;

    @Before
    public void setUp() {
        playwright = Playwright.create();
        browser = playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(true));
        page = browser.newPage();
        registrationPage = new RegistrationPage(page);
    }

    @After
    public void tearDown() {
        if (browser != null) browser.close();
        if (playwright != null) playwright.close();
    }

    @Given("Je suis sur la page d'inscription refondue")
    public void openRegistrationPage() {
        // Simulation de la page cassée (HTML injecté directement pour la démo)
        String brokenHtml = "<html><body>" +
            "<form>" +
            "  <label>Votre Prénom :</label>" +
            "  <!-- ID changé (#input-fname-v2), Classe ajoutée -->" +
            "  <input type='text' id='input-fname-v2' class='form-control-lg' placeholder='Ex: Jean'>" +
            "  <br><br>" +
            "  <!-- Texte changé ('Valider' au lieu de 'Créer'), Classe changée -->" +
            "  <button class='btn-primary-new' type='button' onclick=\"document.getElementById('res').style.display='block'\">" +
            "    Valider l'inscription" +
            "  </button>" +
            "</form>" +
            "<div id='res' style='display:none'>" +
            "  <!-- Tag changé (h2 au lieu de h1), ID changé -->" +
            "  <h2 id='confirm-msg'>Bienvenue Jean, votre compte est prêt.</h2>" +
            "</div>" +
            "</body></html>";
            
        page.setContent(brokenHtml);
    }

    @When("Je saisis le prénom {string}")
    public void enterFirstname(String name) {
        registrationPage.enterFirstname(name);
    }

    @When("Je valide le formulaire")
    public void submit() {
        registrationPage.submitForm();
    }

    @Then("Je dois voir le message de confirmation {string}")
    public void verifyMessage(String msg) {
        registrationPage.checkConfirmationMessage(msg);
    }
}
