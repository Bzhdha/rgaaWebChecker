Feature: Inscription Utilisateur (Démonstration Auto-Healing)

  Scenario: Inscription complète avec DOM instable
    Given Je suis sur la page d'inscription refondue
    When Je saisis le prénom "Jean"
    And Je valide le formulaire
    Then Je dois voir le message de confirmation "Bienvenue"
