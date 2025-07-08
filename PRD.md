### **Product Requirements Document (PRD): Card Arbitrage Finder**

### **1. Introduction & Problem Statement**

The global market for Magic: The Gathering cards is fragmented, with significant price discrepancies between different regions and vendors, most notably between Europe (Cardmarket) and North America (Card Kingdom). For players and investors in Chile, identifying these opportunities is complicated by the need to convert prices from both US Dollars and Euros into Chilean Pesos (CLP) to understand the true price difference.

This project specifies a web application that automates the discovery of these arbitrage opportunities by fetching prices, converting them to CLP, and highlighting the most significant gaps.

### **2. Project Goal & Objective**

To develop a modular, two-step web application that, given a user-defined number of popular Commander cards, identifies the cards with the **greatest price difference in Chilean Pesos (CLP)**. The tool will calculate this difference by comparing the Card Kingdom price (highest) against the Cardmarket price (lowest) after currency conversion.

The primary objective is to provide users with a sorted, actionable list of potential arbitrage opportunities, calculated and displayed entirely in their local currency (CLP).

### **3. Scope**

#### **3.1. In-Scope**

* **Step 1: Card List Generation**
    * The application will scrape the EDHREC "Top Cards" page for the Commander format.
    * The user will specify the number of cards (N) to retrieve.
    * The application will display the resulting list of N cards to the user and wait for the next action.

* **Step 2: Price Analysis & Arbitrage Calculation**
    * Upon user request, the application will use the **Scryfall API** to get pricing data for each card from Cardmarket (in EUR) and Card Kingdom (in USD).
    * The application will use a **third-party currency exchange rate API** (e.g., Frankfurter.app) to fetch the latest conversion rates for USD to CLP and EUR to CLP.
    * It will convert both the Cardmarket and Card Kingdom prices to CLP.
    * It will calculate the arbitrage difference: `Price_Card_Kingdom (CLP) - Price_Cardmarket (CLP)`.
    * The final data will be presented in a clear, **sortable table**, showing:
        * Card Name
        * Card Kingdom Price (CLP)
        * Cardmarket Price (CLP)
        * Price Difference (CLP)
    * The table will be **sorted by default** to show the largest positive price differences at the top.

* **Technology:** The application will be built with Python and Streamlit.

#### **3.2. Out-of-Scope**

* **Overhead Costs:** The calculation will not include shipping costs, taxes, marketplace fees, or import duties. It is a raw price comparison.
* **Advanced Filtering:** The tool will not filter by card condition, language, or foiling.
* **Other Currencies:** The application will only convert to CLP.

### **4. Modular Architecture & User Flow**

The application will guide the user through a clear, sequential process:

1.  **Input:** The user is presented with **Step 1**. They enter a number (N) and click a button ("Get Top Cards").
2.  **Step 1 Complete (Card List):** The app fetches the data from EDHREC, displays a success message, and shows the list of N card names within an expander. A new button for **Step 2** ("Find Arbitrage Opportunities") appears.
3.  **Step 2 Complete (Price Analysis):** After the user clicks the second button, the app performs all API calls (Scryfall, Currency), calculates the conversions and differences, and displays the final, sorted table of results.

### **5. Functional Requirements (User Stories)**

| ID    | User Story                                                                                                   | Acceptance Criteria                                                                                                                                                                                                                                                             |
| :---- | :----------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FR1** | As a user, I want to specify a number 'N' and click a button to get a list of the top N Commander cards.       | - The UI presents a numeric input field for N.<br>- A button ("Get Top Cards") triggers the EDHREC scraping process.<br>- The app displays a loading indicator ("spinner") during the process.                                                                   |
| **FR2** | As a user, after the card list is generated, I want to see it displayed clearly before proceeding.             | - A success message is shown.<br>- A new section for Step 2 appears.<br>- The list of fetched cards is available for viewing inside an expander.<br>- A new primary button ("Find Arbitrage Opportunities") is displayed.                                          |
| **FR3** | As a user, I want to click a button to fetch prices and convert them to CLP to find the best opportunities.   | - The button triggers API calls to Scryfall for prices and to a currency exchange API for rates.<br>- The app displays a progress bar showing the card-by-card processing status.<br>- The app calculates the CLP equivalent for both the USD and EUR prices. |
| **FR4** | As a user, I want to see the results in a table that is **sorted to show me the best opportunities in CLP**.    | - The UI displays a table with columns: "Card Name", "Card Kingdom Price (CLP)", "Cardmarket Price (CLP)", and "Difference (CLP)".<br>- The "Difference (CLP)" column is color-coded (e.g., green for positive, red for negative).<br>- The table is sorted in descending order based on the "Difference (CLP)" column by default. |
| **FR5** | As a user, I want to be notified if an error occurs at any step.                                              | - If EDHREC, Scryfall, or the currency API cannot be reached, a clear error message is shown to the user in the UI.                                                                                                                                  |

### **6. Technical Implementation Assumptions**

* **Data Source (Card List):** Relies on **web scraping** EDHREC. This is fragile and may require maintenance if the site's structure changes.
* **Data Source (Pricing):** Relies on the public **Scryfall API**. This is stable and the preferred method for price data.
* **Data Source (Currency Rates):** Relies on a free, public API like **Frankfurter.app**. This is an external dependency.
* **Frontend:** The UI will be developed using **Streamlit**, leveraging session state to pass data between steps.