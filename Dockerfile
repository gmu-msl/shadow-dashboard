FROM node:20

# Create app directory
WORKDIR /usr/src/app

# install python3-pip and tshark
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y python3-pip tshark \
    && rm -rf /var/lib/apt/lists/*

# Copy package.json and package-lock.json
COPY package*.json ./

# Copy python requirements
COPY processors/preprocess-python/requirements.txt /usr/src/app/processors/preprocess-python/requirements.txt

# install python dependencies
RUN pip3 install -r /usr/src/app/processors/preprocess-python/requirements.txt --break-system-packages

# Install app dependencies
RUN npm install

# Bundle app source
COPY . .

# Expose port 3000
EXPOSE 3000

# Run the app
CMD [ "npm", "start" ]