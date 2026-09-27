const express = require("express");
const cors = require("cors");
const { MongoClient } = require("mongodb");

const app = express();

app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 10000;

const MONGODB_USER = process.env.MONGODB_USER;
const MONGODB_PASSWORD = process.env.MONGODB_PASSWORD;
const MONGODB_HOST = process.env.MONGODB_HOST;
const MONGODB_DATABASE = process.env.MONGODB_DATABASE;

let mongoClient = null;

function getMongoUri() {
    if (!MONGODB_USER || !MONGODB_PASSWORD || !MONGODB_HOST) {
        return null;
    }

    return (
        "mongodb+srv://" +
        encodeURIComponent(MONGODB_USER) +
        ":" +
        encodeURIComponent(MONGODB_PASSWORD) +
        "@" +
        MONGODB_HOST +
        "/?appName=Alfaomega"
    );
}

app.get("/", (req, res) => {
    res.json({
        app: "ALFA OMEGA TRADING",
        service: "server",
        status: "online"
    });
});

app.get("/api/health", async (req, res) => {
    const result = {
        app: "ALFA OMEGA TRADING",
        service: "server",
        status: "online",
        mongodb: "unknown",
        timestamp: new Date().toISOString()
    };

    try {
        const uri = getMongoUri();

        if (!uri) {
            result.mongodb = "not_configured";
            return res.status(503).json(result);
        }

        if (!mongoClient) {
            mongoClient = new MongoClient(uri);
            await mongoClient.connect();
        }

        await mongoClient
            .db(MONGODB_DATABASE)
            .command({ ping: 1 });

        result.mongodb = "connected";

        res.json(result);

    } catch (error) {
        result.mongodb = "error";

        res.status(503).json({
            ...result,
            error: error.message
        });
    }
});

app.listen(PORT, "0.0.0.0", () => {
    console.log(
        "ALFA OMEGA TRADING server escuchando en puerto " + PORT
    );
});
