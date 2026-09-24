# Ecommerce Analytics Dashboard
### Tracy Sandoval - C964 Capstone Part C

### Prerequisites
- npm
- node 20.19 or higher
- python 3.12 or higher
- uv

### Step 1. Open the codebase locally
Unzip the folder containing the codebase, and open the unzipped project in your IDE.

    All of the following terminal commands must be run from the project's root.

### Step 2. Install dependencies from the root
Open a terminal and run `npm install`.

### Step 3. Seed the mock database and run the data processing  pipeline
Open a terminal and run `npm run db:seed` to set up the raw datasets this may take a moment since it will set up the python environment as well, then run `npm run db:pipeline` to process the raw datasets though the data processing pipeline.

### Step 4. Train the demand prediction ml model
Open a terminal and run `npm run ml:train` to train the machine learning model and run `npm run ml:evaluate` to evaluate the model's accuracy using MAE. 

### Step 5. Run the project
Open a terminal and run `npm run dev` Using turborepo I have it set up so that this one command starts up the frontend and backend together.

### Step 6. Test the application in the browser
 You can now open the project in the browser at http://localhost:5173/ this may vary if something is already running on that port, so it is also provided as a link in the terminal when you run the project, all you need to do is ctrl click the link.