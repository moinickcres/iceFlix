module IceFlix {

    ///////////// Errors /////////////

    // Raised if provided authentication token is wrong
    // Also raised if invalid user/password
    exception Unauthorized { };
    
    // Raised if provided media ID is not found
    exception WrongMediaId { string id; };

    // Raised if some item is requested but currently unavailable
    exception TemporaryUnavailable { };

    ///////////// Media server related interfaces /////////////

    // Handle media stream
    interface StreamController {
        string getSDP(string authentication, int port) throws Unauthorized;
        string getSyncTopic();
        void refreshAuthentication(string authentication) throws Unauthorized;
        void stop();
    }

    // StreamController requests channel
    interface StreamerSync {
        void requestAuthentication();
    }

    // Handle media storage
    interface StreamProvider {
        StreamController* getStream(string id, string authentication) throws Unauthorized, WrongMediaId;
        bool isAvailable(string id);
        void reannounceMedia();
    }

    // StreamProvider announcements channel
    interface StreamAnnounces {
        void newMedia(string id, string initialName, string providerId);
    }

    ///////////// Custom Types /////////////

    // List of strings
    sequence<string> StringList;

    // Media info
    struct MediaInfo {
        string name;
        StringList tags;
     }

    // Media location
    struct Media {
        string id;
        StreamProvider *provider;
        MediaInfo info;
    }
   
    ///////////// Catalog server /////////////
   
    interface MediaCatalog {
        Media getTile(string id) throws WrongMediaId, TemporaryUnavailable;
        StringList getTilesByName(string name, bool exact);
        StringList getTilesByTags(StringList tags, bool includeAllTags);
 
        void renameTile(string id, string name, string authentication) throws Unauthorized, WrongMediaId;
        void addTags(string id, StringList tags, string authentication) throws Unauthorized, WrongMediaId;
        void removeTags(string id, StringList tags, string authentication) throws Unauthorized, WrongMediaId;
    }

    ///////////// Auth server /////////////

    interface Authenticator {
        string refreshAuthorization(string user, string passwordHash) throws Unauthorized;
        bool isAuthorized(string authentication);
    }

    interface TokenRevocation {
        void revoke(string authentication);
    }

    ///////////// Main server /////////////

    interface Main {
        Authenticator* getAuthenticator() throws TemporaryUnavailable;
        MediaCatalog* getCatalogService() throws TemporaryUnavailable;
    }

    interface ServiceAvailability {
        void catalogService(MediaCatalog* service, string id);
        void authenticationService(Authenticator* service, string id);
        void mediaService(StreamProvider* service, string id);
    }
}