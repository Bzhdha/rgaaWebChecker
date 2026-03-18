package com.rgaa.framework.core;

import java.util.HashMap;
import java.util.Map;

/**
 * Modèle de données décrivant un élément web attendu.
 * Ces informations permettent à l'algorithme de retrouver l'élément
 * même si son sélecteur CSS technique a changé.
 */
public class ElementDescriptor {
    private String tagName;
    private String id;
    private String text;
    private String className;
    private Map<String, String> attributes = new HashMap<>();

    public ElementDescriptor(String tagName, String id, String text) {
        this.tagName = tagName;
        this.id = id;
        this.text = text;
    }

    // Builders pour faciliter la création dans les Page Objects
    public ElementDescriptor withClass(String className) {
        this.className = className;
        return this;
    }
    
    public ElementDescriptor withAttribute(String key, String value) {
        this.attributes.put(key, value);
        return this;
    }

    // Getters
    public String getTagName() { return tagName; }
    public String getId() { return id; }
    public String getText() { return text; }
    public String getClassName() { return className; }
    public Map<String, String> getAttributes() { return attributes; }
}
