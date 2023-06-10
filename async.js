async function sendCSV() {
        try {
            const uuid = uuidv4();
            const url = "http://34.31.14.214:8443/api/upload";
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ uuid: uuid, csvFile: parsedData }),
            });

            const data = await response.json();

            if (data.uuid == uuid) {
                pollStatus(uuid);
            }
        } catch (error) {
            console.error(error);
        }
    }