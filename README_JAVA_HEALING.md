# Module d'Auto-Healing pour Playwright (Java)

Ce module fournit une capacité de "guérison automatique" (self-healing) pour vos tests automatisés Playwright. Lorsqu'un sélecteur ne trouve plus son élément (dû à un changement de code, refonte UI, etc.), ce module analyse le DOM actuel pour retrouver l'élément le plus probable en utilisant une logique floue (Fuzzy Logic).

## 📁 Structure

Le code source se trouve dans `java_src/com/rgaa/autohealing/` :
1.  `DomHealer.java` : Le moteur d'analyse (injecte du JS intelligent dans le navigateur).
2.  `ElementDescriptor.java` : La classe pour décrire l'élément recherché.

## 🚀 Intégration dans votre projet

### 1. Copier les fichiers
Copiez le package `com.rgaa.autohealing` dans votre dossier source Java (ex: `src/main/java/`).

### 2. Exemple d'utilisation (Snippet)

Voici comment modifier vos méthodes de test ou votre framework de page ("Page Object") pour utiliser l'auto-healing.

```java
import com.microsoft.playwright.*;
import com.rgaa.autohealing.DomHealer;
import com.rgaa.autohealing.ElementDescriptor;

public class TestBase {
    protected Page page;
    protected DomHealer healer = new DomHealer();

    // Méthode wrapper pour cliquer avec auto-healing
    protected void smartClick(String selector, ElementDescriptor expectedElement) {
        try {
            // Tentative normale
            page.locator(selector).click(new Locator.ClickOptions().setTimeout(2000));
        } catch (TimeoutError | ElementHandle.ElementNotFoundException e) {
            System.out.println("⚠️ Sélecteur '" + selector + "' introuvable. Tentative d'auto-healing...");
            
            // Appel au module d'auto-healing
            Locator healedLocator = healer.findBestMatch(page, expectedElement);
            
            if (healedLocator != null) {
                System.out.println("✅ Élément retrouvé ! Clic sur le nouvel élément.");
                
                // On interagit avec le nouvel élément trouvé
                healedLocator.click();
                
                // TODO: Enregistrer ce nouveau sélecteur pour mettre à jour le test
            } else {
                throw new RuntimeException("❌ Auto-healing échoué. Élément définitivement perdu.");
            }
        }
    }
}
```

### 3. Créer un descripteur

Idéalement, votre framework de test devrait stocker non seulement le sélecteur, mais aussi quelques métadonnées sur l'élément (ID, texte, tag) pour permettre la recherche floue.

```java
// Exemple de définition d'un bouton de validation
ElementDescriptor btnValider = new ElementDescriptor();
btnValider.setTagName("button");
btnValider.setId("btn-validate-order"); // L'ID original
btnValider.setText("Valider la commande");

// Utilisation
smartClick("#btn-validate-order", btnValider);
```

## ⚙️ Fonctionnement Technique

1.  Le module `DomHealer` reçoit la demande.
2.  Il injecte un script JavaScript optimisé dans le contexte de la page (`page.evaluate()`).
3.  Le script parcourt le DOM et calcule un **score de similarité** pour chaque élément candidat en comparant :
    *   Le tag (ex: `<a>` vs `<button>`)
    *   L'ID (Distance de Levenshtein)
    *   Le texte visible
    *   Les classes CSS
4.  Le script retourne le sélecteur CSS unique du meilleur candidat (si le score > 60%).
5.  Playwright récupère ce sélecteur et peut continuer l'interaction.
