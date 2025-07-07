### **Product Requirements Document (PRD): Automated Cardmarket Seller Finder (Phase 1: Single Card)**

  * **Document Version:** 1.0
  * **Date:** July 7, 2025
  * **Author:** Gemini
  * **Status:** Draft

-----

### **1. Introduction & Problem Statement**

Magic: The Gathering players and collectors in Spain who purchase single cards online face a time-consuming and inefficient process. When trying to find the best deal for a specific card, they must manually browse a marketplace like Cardmarket (MKM), identify sellers who ship to Spain, compare individual card prices, and then investigate each seller's specific shipping costs to their location. This process is prone to error and often results in the user not finding the absolute lowest total cost (card price + shipping).

This project aims to automate this process. This initial phase (Phase 1) will create a minimum viable product (MVP) focused on solving this problem for a **single card**, laying the foundation for a more complex multi-card optimization tool in the future.

### **2. Project Goal & Objective**

To develop a simple web application that, given a single Magic: The Gathering card name, automatically identifies the seller on Cardmarket offering the lowest total price, including shipping to Barcelona, Spain.

  * **Primary Metric for "Best":** Lowest Total Price, calculated as:
    $Total Price = Price\_{card} + Price\_{shipping\_to\_ES}$
  * **Key Objective:** Reduce the time and effort for a user to find the optimal seller for a single card from several minutes of manual searching to a few seconds of automated processing.

### **3. Scope**

#### **3.1. In-Scope (MVP for Phase 1)**

  * **Input:** A single text field for the user to enter one card name.
  * **Data Source:** Cardmarket (https://www.google.com/search?q=mkm.cardmarket.com) will be the sole source of pricing and seller data.
  * **Core Logic:**
    1.  Accept a card name as input.
    2.  Query Cardmarket for all available listings of that card.
    3.  Filter the results to include **only professional and power sellers** who explicitly ship to **Spain**. (This reduces complexity by avoiding private sellers with less predictable shipping rules).
    4.  For each valid listing, extract the card price and the shipping cost to Spain.
    5.  Calculate the total price for each listing.
    6.  Identify and display the single best offer (lowest total price).
  * **Output Display:** The application will clearly display:
      * Seller's Username
      * Card Price
      * Shipping Price
      * Total Calculated Price
      * A direct link to the seller's offer page on Cardmarket.
  * **Technology:** The application will be built using Python for the backend logic (scraping/API interaction) and Streamlit for the user interface, as per the initial investigation.

#### **3.2. Out-of-Scope (for Future Phases)**

  * **Multi-Card Optimization:** This PRD does **not** cover the optimization of a shopping cart with multiple cards from one or more sellers. This is the primary goal for Phase 2.
  * **Advanced Filtering:** No filtering by card condition (e.g., Near Mint, Played), language, foiling, or seller reputation/rating. The app will default to the cheapest available offering that meets the core criteria.
  * **Other Marketplaces:** The tool will not query other platforms like TCGPlayer, eBay, or local stores.
  * **User Accounts:** No functionality for user login, saving searches, or creating watchlists.

### **4. User Persona**

**Name:** Pau
**Location:** Barcelona, Spain
**Bio:** Pau is an avid Magic player who regularly updates his decks. He typically buys 5-10 single cards online every month. He values his time and wants to get the best possible price without spending 30 minutes cross-referencing sellers and shipping costs on Cardmarket. He is tech-savvy enough to use a simple web app but is not a programmer.

### **5. Functional Requirements (User Stories)**

| ID | User Story | Acceptance Criteria |
| :--- | :--- | :--- |
| **FR1** | As a user, I want to enter the name of a Magic card into a search box. | - The UI presents a clear text input field.\<br\>- The application can handle card names with special characters (e.g., "Sol Ring", "Æther Vial").\<br\>- A "Search" button initiates the process. |
| **FR2** | As a user, I want the application to automatically find all sellers on Cardmarket who ship to Spain. | - The backend logic correctly identifies sellers with shipping methods available for Spain.\<br\>- The system correctly excludes sellers who do not ship to Spain. |
| **FR3** | As a user, I want the application to calculate the total cost (card + shipping) for each offer. | - The system accurately extracts the card's listed price.\<br\>- The system accurately finds and extracts the specific shipping cost to Spain.\<br\>- The sum $Price\_{card} + Price\_{shipping}$ is calculated correctly. |
| **FR4** | As a user, I want to see the single best offer presented clearly. | - The UI displays the Seller's Name, Card Price, Shipping Price, and Total Price for the best offer found.\<br\>- The UI provides a clickable hyperlink that takes me directly to that offer on the Cardmarket website. |
| **FR5** | As a user, I want to be notified if the card cannot be found or if no sellers ship to Spain. | - If the card name yields no results on Cardmarket, a message like "Card not found. Please check spelling." is displayed.\<br\>- If the card is found but no sellers ship to Spain, a message like "No sellers found that ship to your location." is displayed. |

### **6. Technical Implementation Assumptions (from prior investigation)**

  * **Data Retrieval:** The system will use web scraping techniques with Python libraries such as `requests` and `BeautifulSoup4` or `lxml`.
      * **Challenge:** This is dependent on Cardmarket's website structure. Changes to their site could break the scraper. An official API would be preferable if available and accessible, but scraping is the assumed method for this MVP.
      * **Mitigation:** The scraper must be built with robust error handling and logging. It should use a proper User-Agent and respect `robots.txt` to be an ethical client. Rate limiting should be implemented to avoid overwhelming the server.
  * **Frontend:** The UI will be developed using Streamlit, allowing for rapid development of a simple, interactive data application.
  * **Deployment:** The application will be deployed on a platform compatible with Streamlit (e.g., Streamlit Community Cloud, Heroku, or a private server).

### **7. Success Metrics**

  * **Task Completion Rate:** \>95% of searches for valid, in-stock cards return a result.
  * **Accuracy:** For a given card, the result provided by the app matches the best price a user can find manually on Cardmarket in \>90% of cases.
  * **Performance:** The time from clicking "Search" to displaying a result is under 10 seconds.
  * **User Feedback (Qualitative):** Users confirm that the tool saves them significant time and effort compared to the manual process.

### **8. Roadmap**

  * **Phase 1 (This PRD):** Development and release of the single-card seller finder MVP.
  * **Phase 2 (Future):** Introduce multi-card list functionality. The user will be able to input a list of cards, and the tool will find the best combination of sellers to minimize total cost (a significantly more complex "knapsack" or "set cover" type problem).
  * **Phase 3 (Future):** Incorporate advanced filtering (condition, language, foil), seller ratings, and potentially other data sources.